from api.models import Job, Task
from api.models import Member


def create_member(name: str, surname: str, age: str) -> str:
    age_clean = age.strip()
    if age_clean not in ["ofLegalAge", "underage"]:
        if "voll" in age_clean.lower() or "18" in age_clean:
            age_clean = "ofLegalAge"
        else:
            age_clean = "underage"

    member = Member.objects.create(
        name=name.strip(), surname=surname.strip(), age=age_clean
    )

    return f"Erfolg: Das Mitglied {member.name} {member.surname} (ID: {member.id}, Status: {member.age}) wurde erfolgreich in der Datenbank angelegt."


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
        Your name is Dieter.ai.
        This event takes place in Altheim, Niederbayern, Germany, on September 05 - 06 2026 between 18:30 and 02:00.
        It is organized by a groud of local volunteers and helpers, who are all members of the KLJB Altheim.
        Please only answer in German.
        Keep yourself as short as possible and stay helpful and friendly at the same time.
        Your task is to answer questions only based on the current database information.
        If there are no data available for a specific question (e.g., a person does not exist), please inform the user politely that there is no data available in the database.
        If the user asks to add or create a new person, use the `create_member` tool.
        If necessary parameters (first name, surname, or age) are missing, ask the user for clarification before executing the function.
        Never make up any data or parameters the user has not explicitly provided.
        The following information is available in the database:

        --- CURRENT JOBS AND SHIFTS ---
        {jobs_knowledge}

        --- AVAILABLE MEMBERS AND WORKERS ---
        {members_knowledge}

        --- TO-DO LIST AND PREPARATION TASKS ---
        {tasks_knowledge}
    """
    return system_instruction
