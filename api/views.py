from rest_framework import status, viewsets
from .models import Job, Member, Task
from .serializers import JobSerializer, MemberSerializer, TaskSerializer
from rest_framework.response import Response
from django.conf import settings
from google import genai


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


class GeminiChatView(viewsets.ViewSet):
    def create(self, request):
        question = request.data.get("question", "")

        if not question:
            return Response(
                {"error": "Keine Frage angegeben."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=question,
                config={
                    "system_instruction": "Please only answer in German. Keep yourself as short as possible."
                },
            )

            return Response({"output_text": response.text})

        except Exception as e:
            print("Gemini API Error:", e)
            return Response(
                {"error": "Fehler beim Abrufen der Antwort. Bitte versuche es erneut."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
