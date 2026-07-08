from rest_framework import viewsets
from .models import Member, Task
from .serializers import MemberSerializer, TaskSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all().order_by("surname")
    serializer_class = MemberSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
