from django.contrib.auth.models import User
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from google import genai
from google.genai import types
from .serializers import UserSerializer

from api.services.chatbot_tools import (
    assign_member_to_job,
    create_job,
    create_member,
    create_task,
    delete_job,
    delete_member,
    delete_task,
    update_job,
    get_knowledge_base,
    update_task,
)
from .models import Job, Member, Task
from .serializers import JobSerializer, MemberSerializer, TaskSerializer


class JobViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.all().order_by("job")
    serializer_class = JobSerializer

    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.requires_legal_age == "doesRequireLegalAge":
            instance.assigned_members.filter(age="underage").update(job=None)


class MemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Member.objects.all().order_by("surname", "name")
    serializer_class = MemberSerializer


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all().order_by("-moved_at")
    serializer_class = TaskSerializer


class GeminiChatView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[
                    assign_member_to_job,
                    create_job,
                    create_member,
                    create_task,
                    delete_job,
                    delete_member,
                    delete_task,
                    update_job,
                    update_task,
                ],
                temperature=0.15,
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=formatted_contents,
                config=config,
            )

            return Response({"output_text": response.text})

        except Exception as e:
            print(f"Gemini-API-Fehler: {type(e).__name__}: {e}")
            return Response(
                {"error": f"Fehler bei der Kommunikation mit Gemini: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
