from rest_framework import serializers
from .models import Job, Member, Task


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["job", "workers", "requires_legal_age", "id"]

    def validate_job(self, value):
        queryset = Job.objects.filter(job__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Eine Aufgabe mit diesem Namen existiert bereits."
            )

        return value


class MemberSerializer(serializers.ModelSerializer):
    job = serializers.SlugRelatedField(read_only=True, slug_field="job")

    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        source="job",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Member
        fields = ["surname", "name", "age", "job", "job_id", "id"]

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", None))
        surname = attrs.get("surname", getattr(self.instance, "surname", None))

        if name and surname:
            queryset = Member.objects.filter(name__iexact=name, surname__iexact=surname)

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "Ein Mitglied mit diesem Namen und Nachnamen existiert bereits."
                        ]
                    }
                )

        return attrs

    def validate_job_id(self, value):
        if value is None:
            return value

        member_age = self.initial_data.get("age") or (
            self.instance.age if self.instance else None
        )

        if (
            value.requires_legal_age == "doesRequireLegalAge"
            and member_age == "underage"
        ):
            raise serializers.ValidationError(
                "Dieser Job erfordert Volljährigkeit. Das Mitglied ist minderjährig."
            )

        is_already_assigned = self.instance and self.instance.job_id == value.id

        if not is_already_assigned:
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

    def validate_task(self, value):
        queryset = Task.objects.filter(task__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Eine Aufgabe mit diesem Namen existiert bereits."
            )

        return value
