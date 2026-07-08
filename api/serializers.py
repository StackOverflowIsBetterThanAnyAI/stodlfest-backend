from rest_framework import serializers
from .models import Member, Task


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["surname", "name", "age", "job", "id"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["created_at", "id", "task", "description", "priority", "finished"]
