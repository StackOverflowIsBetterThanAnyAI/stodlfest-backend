from rest_framework import serializers
from .models import Job, Member, Task


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["job", "workers", "requires_legal_age", "id"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["surname", "name", "age", "job", "id"]

    def validate_job(self, value):
        if value is None:
            return value

        request_age = self.initial_data.get("age")

        if value.requires_legal_age and request_age == "underage":
            raise serializers.ValidationError(
                "Dieser Job erfordert Volljährigkeit. Das Mitglied ist minderjährig."
            )

        current_workers_count = value.assigned_members.count()
        if current_workers_count >= value.workers:
            raise serializers.ValidationError(
                f"Dieser Job ist bereits voll besetzt (Maximal {value.workers} Helfer)."
            )

        return value


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["moved_at", "id", "task", "description", "priority", "finished"]
