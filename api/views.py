from rest_framework import viewsets
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
    queryset = Member.objects.all().order_by("surname")
    serializer_class = MemberSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-moved_at")
    serializer_class = TaskSerializer
