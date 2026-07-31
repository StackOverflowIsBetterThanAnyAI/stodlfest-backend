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
        chat_history = request.data

        if not isinstance(chat_history, list) or not chat_history:
            return Response(
                {"error": "Invalid Chat History."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            return Response(
                {"error": "No API Key."},
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
                    {"error": "No valid Question."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=formatted_contents,
                config={
                    "system_instruction": "Please only answer in German. Keep yourself as short as possible."
                },
            )

            return Response({"output_text": response.text})

        except Exception as e:
            print(f"Gemini API Error: {type(e).__name__}: {e}")
            return Response(
                {"error": f"Error while communicating with Gemini: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
