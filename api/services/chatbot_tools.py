from api.models import Job, Member, Task


def assign_member_to_job(member_name: str, job_name: str = "") -> str:
    member_clean = member_name.strip()
    members = list(
        Member.objects.filter(name__iexact=member_clean)
        | Member.objects.filter(surname__iexact=member_clean)
    )

    if not members:
        parts = member_clean.split()
        if len(parts) >= 2:
            members = list(
                Member.objects.filter(name__iexact=parts[0], surname__iexact=parts[1])
            )

    if not members:
        members = list(
            Member.objects.filter(name__icontains=member_clean)
            | Member.objects.filter(surname__icontains=member_clean)
        )

    if not members:
        return f"Fehler: Kein Mitglied gefunden, das zu '{member_clean}' passt."

    if len(members) > 1:
        found_names = [f"{m.name} {m.surname}" for m in members]
        return f"Fehler: Es wurden mehrere Mitglieder gefunden ({', '.join(found_names)}). Bitte gib den vollständigen Namen an."

    member_obj = members[0]
    full_member_name = f"{member_obj.name} {member_obj.surname}"

    job_clean = job_name.strip().lower() if job_name else ""
    if not job_clean or any(
        remove_kw in job_clean
        for remove_kw in ["kein", "entfernen", "löschen", "none", "abmelden"]
    ):
        if member_obj.job is None:
            return f"Hinweis: {full_member_name} ist aktuell keiner Aufgabe zugewiesen."

        old_job_title = member_obj.job.job
        member_obj.job = None
        member_obj.save()
        return f"Erfolg: {full_member_name} wurde erfolgreich aus der Aufgabe '{old_job_title}' entfernt."

    jobs = list(Job.objects.filter(job__iexact=job_name.strip()))
    if not jobs:
        jobs = list(Job.objects.filter(job__icontains=job_name.strip()))

    if not jobs:
        return f"Fehler: Keine Aufgabe gefunden, die zu '{job_name}' passt."

    if len(jobs) > 1:
        found_jobs = [f"'{j.job}'" for j in jobs]
        return f"Fehler: Es wurden mehrere Aufgaben gefunden ({', '.join(found_jobs)}). Bitte spezifiziere die Aufgabe genauer."

    job_obj = jobs[0]

    if member_obj.job == job_obj:
        return f"Hinweis: {full_member_name} ist bereits der Aufgabe '{job_obj.job}' zugewiesen."

    if (
        job_obj.requires_legal_age == "doesRequireLegalAge"
        and member_obj.age == "underage"
    ):
        return (
            f"Fehler: {full_member_name} ist minderjährig. "
            f"Die Aufgabe '{job_obj.job}' erfordert jedoch Volljährigkeit!"
        )

    current_count = job_obj.assigned_members.count()
    if current_count >= job_obj.workers:
        return (
            f"Fehler: Die Aufgabe '{job_obj.job}' ist bereits voll besetzt "
            f"({current_count}/{job_obj.workers} Plätze belegt)."
        )

    member_obj.job = job_obj
    member_obj.save()

    return f"Erfolg: {full_member_name} wurde erfolgreich der Aufgabe '{job_obj.job}' zugewiesen."


def create_job(
    job: str, workers: int = 1, requires_legal_age: str = "doesNotRequireLegalAge"
) -> str:
    job_clean = job.strip()

    existing_job = Job.objects.filter(job__iexact=job_clean).first()
    if existing_job:
        return (
            f"Hinweis: Eine Aufgabe mit dem Namen '{job_clean}' existiert bereits. "
            f"Es wurde keine neue Aufgabe angelegt."
        )

    try:
        workers_count = int(workers)
        workers_count = max(1, min(15, workers_count))
    except (ValueError, TypeError):
        workers_count = 1

    legal_age_clean = requires_legal_age.strip()
    if (
        "doesRequireLegalAge" in legal_age_clean
        or "ja" in legal_age_clean.lower()
        or "voll" in legal_age_clean.lower()
    ):
        legal_age_val = "doesRequireLegalAge"
    else:
        legal_age_val = "doesNotRequireLegalAge"

    job_instance = Job.objects.create(
        job=job_clean,
        workers=workers_count,
        requires_legal_age=legal_age_val,
    )

    legal_str = (
        "Ja" if job_instance.requires_legal_age == "doesRequireLegalAge" else "Nein"
    )
    return f"Erfolg: Die Aufgabe '{job_instance.job}' (Benötigte Helfer: {job_instance.workers}, Volljährigkeit: {legal_str}) wurde erfolgreich angelegt."


def update_job(
    job_identifier: str,
    new_title: str = "",
    workers: int = None,
    requires_legal_age: str = "",
) -> str:
    job_clean = job_identifier.strip()
    jobs = list(Job.objects.filter(job__iexact=job_clean))

    if not jobs:
        jobs = list(Job.objects.filter(job__icontains=job_clean))

    if not jobs:
        return f"Fehler: Keine Aufgabe gefunden, die zu '{job_clean}' passt."

    if len(jobs) > 1:
        found_titles = [f"'{j.job}'" for j in jobs]
        return f"Fehler: Es wurden mehrere Aufgaben gefunden ({', '.join(found_titles)}). Bitte spezifiziere die Aufgabe genauer."

    job_obj = jobs[0]
    updated_fields = []

    if new_title and new_title.strip():
        old_title = job_obj.job
        job_obj.job = new_title.strip()
        updated_fields.append(f"Titel von '{old_title}' zu '{job_obj.job}' geändert")

    if workers is not None:
        try:
            workers_count = int(workers)
            workers_count = max(1, min(15, workers_count))
            job_obj.workers = workers_count
            updated_fields.append(f"Benötigte Helfer auf {workers_count} gesetzt")
        except (ValueError, TypeError):
            pass

    if requires_legal_age and requires_legal_age.strip():
        legal_clean = requires_legal_age.strip().lower()

        if any(
            neg in legal_clean
            for neg in ["nein", "minderjährig", "underage", "doesnot"]
        ):
            new_val = "doesNotRequireLegalAge"
            legal_str = "Nein (Auch Minderjährige)"
        else:
            new_val = "doesRequireLegalAge"
            legal_str = "Ja (Nur Volljährige)"

        if job_obj.requires_legal_age != new_val:
            job_obj.requires_legal_age = new_val
            updated_fields.append(
                f"Volljährigkeit erforderlich auf '{legal_str}' geändert"
            )

    if not updated_fields:
        return f"Hinweis: Für den Job '{job_obj.job}' wurden keine auswertbaren Änderungen übergeben."

    job_obj.save()

    return f"Erfolg: Die Aufgabe '{job_obj.job}' wurde aktualisiert: {', '.join(updated_fields)}."


def delete_job(job_identifier: str) -> str:
    job_clean = job_identifier.strip()
    jobs = list(Job.objects.filter(job__iexact=job_clean))

    if not jobs:
        jobs = list(Job.objects.filter(job__icontains=job_clean))

    if not jobs:
        return f"Fehler: Keine Aufgabe gefunden, die zu '{job_clean}' passt."

    if len(jobs) > 1:
        found_titles = [f"'{j.job}'" for j in jobs]
        return f"Fehler: Es wurden mehrere passende Aufgaben gefunden: {', '.join(found_titles)}. Bitte gib den Titel genauer an."

    job_to_delete = jobs[0]
    title = job_to_delete.job
    job_to_delete.delete()

    return f"Erfolg: Die Aufgabe '{title}' wurde erfolgreich gelöscht."


def create_task(
    task: str, priority: str = "middle", description: str = "", finished: bool = False
) -> str:
    task_clean = task.strip()

    existing_task = Task.objects.filter(task__iexact=task_clean).first()

    if existing_task:
        return (
            f"Hinweis: Eine Aufgabe mit dem Namen '{task_clean}' existiert bereits. "
            f"Es wurde keine neue Aufgabe angelegt."
        )

    priority_clean = priority.strip().lower()

    prio_map = {
        "hoch": "high",
        "high": "high",
        "mittel": "middle",
        "middle": "middle",
        "niedrig": "low",
        "low": "low",
    }

    final_priority = prio_map.get(priority_clean, "middle")

    task_instance = Task.objects.create(
        task=task_clean,
        priority=final_priority,
        description=description.strip(),
        finished=finished,
    )

    return f"Erfolg: Die Aufgabe '{task_instance.task}' mit der Priorität {task_instance.priority}) wurde erfolgreich angelegt."


def update_task(
    task_identifier: str,
    new_title: str = "",
    description: str = "",
    priority: str = "",
    finished: bool = None,
) -> str:
    task_clean = task_identifier.strip()
    tasks = list(Task.objects.filter(task__iexact=task_clean))

    if not tasks:
        tasks = list(Task.objects.filter(task__icontains=task_clean))

    if not tasks:
        return f"Fehler: Keine Aufgabe gefunden, die zu '{task_clean}' passt."

    if len(tasks) > 1:
        found_titles = [f"'{t.task}'" for t in tasks]
        return f"Fehler: Es wurden mehrere Aufgaben gefunden ({', '.join(found_titles)}). Bitte spezifiziere die Aufgabe genauer."

    task_obj = tasks[0]
    updated_fields = []

    if finished is not None:
        is_finished = finished
        if isinstance(finished, str):
            is_finished = finished.strip().lower() in ["true", "1", "yes", "ja"]

        task_obj.finished = is_finished
        status_text = "erledigt" if is_finished else "wiederhergestellt (offen)"
        updated_fields.append(f"Status auf '{status_text}' gesetzt")

    if new_title and new_title.strip():
        old_title = task_obj.task
        task_obj.task = new_title.strip()
        updated_fields.append(f"Titel von '{old_title}' zu '{task_obj.task}' geändert")

    if description and description.strip():
        task_obj.description = description.strip()
        updated_fields.append("Beschreibung aktualisiert")

    if priority and priority.strip():
        prio_map = {
            "hoch": "high",
            "high": "high",
            "mittel": "middle",
            "middle": "middle",
            "niedrig": "low",
            "low": "low",
        }
        mapped_prio = prio_map.get(priority.strip().lower())

        if mapped_prio:
            task_obj.priority = mapped_prio
            updated_fields.append(f"Priorität auf '{mapped_prio}' geändert")

    if not updated_fields:
        return f"Hinweis: Für die Aufgabe '{task_obj.task}' wurden keine auswertbaren Änderungen übergeben."

    task_obj.save()

    return f"Erfolg: Die Aufgabe '{task_obj.task}' wurde aktualisiert: {', '.join(updated_fields)}."


def delete_task(task_identifier: str) -> str:
    task_clean = task_identifier.strip()
    tasks = list(Task.objects.filter(task__iexact=task_clean))

    if not tasks:
        tasks = list(Task.objects.filter(task__icontains=task_clean))

    if not tasks:
        return f"Fehler: Keine Aufgabe gefunden, die zu '{task_clean}' passt."

    if len(tasks) > 1:
        found_titles = [f"'{t.task}'" for t in tasks]
        return f"Fehler: Es wurden mehrere passende Aufgaben gefunden: {', '.join(found_titles)}. Bitte gib den Titel genauer an."

    task_to_delete = tasks[0]
    title = task_to_delete.task
    task_to_delete.delete()

    return f"Erfolg: Die Aufgabe '{title}' wurde erfolgreich gelöscht."


def create_member(name: str, surname: str, age: str) -> str:
    name_clean = name.strip()
    surname_clean = surname.strip()

    existing_member = Member.objects.filter(
        name__iexact=name_clean, surname__iexact=surname_clean
    ).first()

    if existing_member:
        return (
            f"Hinweis: Ein Mitglied mit dem Namen '{name_clean} {surname_clean}' existiert bereits. "
            f"Es wurde kein neues Mitglied angelegt."
        )

    age_clean = age.strip()
    if age_clean not in ["ofLegalAge", "underage"]:
        if "voll" in age_clean.lower() or "18" in age_clean:
            age_clean = "ofLegalAge"
        else:
            age_clean = "underage"

    member = Member.objects.create(
        name=name_clean, surname=surname_clean, age=age_clean
    )

    return f"Erfolg: Das Mitglied {member.name} {member.surname} (Status: {member.age}) wurde erfolgreich angelegt."


def delete_member(name: str, surname: str = "") -> str:
    name_clean = name.strip()
    surname_clean = surname.strip()

    query = Member.objects.filter(name__iexact=name_clean)
    if surname_clean:
        query = query.filter(surname__iexact=surname_clean)

    members = list(query)

    if not members:
        search_term = f"{name_clean} {surname_clean}".strip()
        return f"Fehler: Kein Mitglied mit dem Namen '{search_term}' gefunden."

    if len(members) > 1:
        found_names = [f"{m.name} {m.surname} (ID: {m.id})" for m in members]
        return (
            f"Fehler: Es wurden mehrere Personen gefunden: {', '.join(found_names)}. "
            "Bitte gib den Nachnamen genauer an."
        )

    member_to_delete = members[0]
    full_name = f"{member_to_delete.name} {member_to_delete.surname}"
    member_to_delete.delete()

    return f"Erfolg: Das Mitglied {full_name} wurde erfolgreich gelöscht."


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
        
        If the user refers to a preparation task for the event, you can use the following tools to manage them:
        If the user refers to job in general, ask the user to clarify if they mean a preparation task or a job /shift during the event.
        If the user asks to add or create a new preparation task, use the `create_task` tool.
        If the user asks to edit or update an existing preparation task, use the `update_task` tool.
        If the user asks to delete an existing preparation task, use the `delete_task` tool.
        If necessary parameters (task, or priority) are missing, ask the user for clarification before executing the function.

        If the user refers to a job / shift during the event, you can use the following tools to manage them:
        If the user asks to add or create a job / shift during the event, use the `create_job` tool.
        If the user asks to edit or update an existing job / shift during the event, use the `update_job` tool.
        If the user asks to delete/remove a job/shift during the event, use the `delete_job` tool.
        If necessary parameters (job, workers, or requires_legal_age) are missing, ask the user for clarification before executing the function.
        
        If the user asks to assign a member to a job or remove a member from a job, use the `assign_member_to_job` tool.
        If necessary parameters (member_name, or job_name) are missing, ask the user for clarification before executing the function.
        If the user wants to unassign / remove the member from their job, pass `job_name="entfernen"` or leave `job_name` empty.

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
