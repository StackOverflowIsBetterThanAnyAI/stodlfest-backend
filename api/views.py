from rest_framework import status, viewsets
from rest_framework.response import Response
from django.conf import settings
from google import genai
from .models import Job, Member, Task
from .serializers import JobSerializer, MemberSerializer, TaskSerializer


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by("job")
    serializer_class = JobSerializer

    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.requires_legal_age == "doesRequireLegalAge":
            instance.assigned_members.filter(age="underage").update(job=None)


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all().order_by("surname", "name")
    serializer_class = MemberSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-moved_at")
    serializer_class = TaskSerializer


def get_knowledge_base():
    jobs = Job.objects.prefetch_related("assigned_members").all()
    job_strings = []

    for j in jobs:
        legal_req = (
            "Ja (Nur Volljährige)"
            if j.requires_legal_age == "doesRequireLegalAge"
            else "Nein (Auch Minderjährige)"
        )
        assigned_members = j.assigned_members.all()
        current_count = assigned_members.count()
        missing_workers = j.workers - current_count

        assigned_names = [f"{m.name} {m.surname}" for m in assigned_members]
        names_str = (
            ", ".join(assigned_names)
            if assigned_names
            else "Keine Helfer bisher zugewiesen"
        )

        job_strings.append(
            f"- Job: '{j.job}' | Benötigte Helfer: {j.workers} | Aktuell zugewiesen: {current_count} ({names_str}) | "
            f"Noch benötigte Helfer: {max(0, missing_workers)} | Volljährigkeit erforderlich: {legal_req}"
        )

    jobs_knowledge = (
        "\n".join(job_strings) if job_strings else "Keine Jobs eingetragen."
    )

    members = Member.objects.select_related("job").all()
    member_strings = []

    for m in members:
        age_str = "Volljährig" if m.age == "ofLegalAge" else "Minderjährig"
        assigned_job = m.job.job if m.job else "Kein Job zugewiesen"

        member_strings.append(
            f"- Mitglied: {m.name} {m.surname} | Alter: {age_str} | Zugewiesene Aufgabe: '{assigned_job}'"
        )

    members_knowledge = (
        "\n".join(member_strings) if member_strings else "Keine Mitglieder eingetragen."
    )

    tasks = Task.objects.all()
    task_strings = []

    priority_map = {"low": "Niedrig", "middle": "Mittel", "high": "Hoch"}

    for t in tasks:
        status_str = "Erledigt" if t.finished else "Ausstehend"
        prio_str = priority_map.get(t.priority, t.priority)
        desc_str = f" | Beschreibung: {t.description}" if t.description else ""

        task_strings.append(
            f"- Aufgabe: '{t.task}' | Status: {status_str} | Priorität: {prio_str}{desc_str}"
        )

    tasks_knowledge = (
        "\n".join(task_strings) if task_strings else "Keine Aufgaben eingetragen."
    )

    system_instruction = f"""
        You are the official, helpful AI assistant for the organization of the Stodlfest.
        This event takes place in Altheim, Niederbayern, Germany, on September 05 - 06 2026 between 18:30 and 02:00.
        It is organized by a groud of local volunteers and helpers, who are all members of the KLJB Altheim.
        Please only answer in German.
        Keep yourself as short as possible and stay helpful and friendly at the same time.
        Your task is to answer questions only based on the current database information.
        If there are no data available for a specific question (e.g., a person does not exist), please inform the user politely that there is no data available in the database.
        The following information is available in the database:

        --- CURRENT JOBS AND SHIFTS ---
        {jobs_knowledge}

        --- AVAILABLE MEMBERS AND WORKERS ---
        {members_knowledge}

        --- TO-DO LIST AND PREPARATION TASKS ---
        {tasks_knowledge}
    """
    return system_instruction


class GeminiChatView(viewsets.ViewSet):
    def create(self, request):
        chat_history = request.data

        if not isinstance(chat_history, list) or not chat_history:
            return Response(
                {"error": "Ungültiger Chat-Verlauf."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            return Response(
                {"error": "Kein API-Schlüssel verfügbar."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            client = genai.Client(api_key=api_key)

            formatted_contents = []
            for entry in chat_history:
                raw_message = entry.get("message", "")
                message = (
                    raw_message.strip() if isinstance(raw_message, str) else raw_message
                )

                if not message:
                    continue

                role = "model" if entry.get("role") == "bot" else "user"
                formatted_contents.append({"role": role, "parts": [{"text": message}]})

            while formatted_contents and formatted_contents[-1]["role"] == "model":
                formatted_contents.pop()

            if not formatted_contents:
                return Response(
                    {"error": "Keine gültige Frage."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            system_instruction = get_knowledge_base()

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=formatted_contents,
                config={"system_instruction": system_instruction},
            )

            return Response({"output_text": response.text})

        except Exception as e:
            print(f"Gemini-API-Fehler: {type(e).__name__}: {e}")
            return Response(
                {"error": f"Fehler bei der Kommunikation mit Gemini: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
