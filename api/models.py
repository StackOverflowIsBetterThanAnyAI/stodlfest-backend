from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class Job(models.Model):
    job = models.CharField(
        "Aufgabe",
        max_length=63,
        unique=True,
        error_messages={"unique": "Eine Arbeit mit diesem Namen existiert bereits."},
    )
    workers = models.PositiveIntegerField(
        "Benötigte Helfer",
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        error_messages={
            "min_value": "Es muss mindestens 1 Helfer zugewiesen werden.",
            "max_value": "Es dürfen maximal 15 Helfer zugewiesen werden.",
        },
    )
    AGE_CHOICES = [
        ("doesRequireLegalAge", "Does Require Legal Age"),
        ("doesNotRequireLegalAge", "Does Not Require Legal Age"),
    ]
    requires_legal_age = models.CharField(
        "Nur für Volljährige", max_length=23, choices=AGE_CHOICES
    )

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Job.objects.get(pk=self.pk)

            if (
                old_instance.requires_legal_age != "doesRequireLegalAge"
                and self.requires_legal_age == "doesRequireLegalAge"
            ):
                self.assigned_members.filter(age="underage").update(job=None)

            if self.workers < old_instance.workers:
                current_members = self.assigned_members.all()
                current_count = current_members.count()

                if current_count > self.workers:
                    excess_amount = current_count - self.workers

                    members_to_remove = current_members.order_by("-surname", "-name")[
                        :excess_amount
                    ]

                    ids_to_remove = [m.id for m in members_to_remove]

                    self.assigned_members.filter(id__in=ids_to_remove).update(job=None)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.job


class Member(models.Model):
    AGE_CHOICES = [
        ("underage", "Underage"),
        ("ofLegalAge", "Of Legal Age"),
    ]

    name = models.CharField("Name", max_length=63)
    surname = models.CharField("Nachname", max_length=63)
    age = models.CharField("Alter", max_length=15, choices=AGE_CHOICES)
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_members",
        verbose_name="Zugewiesene Aufgabe",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "surname"],
                name="unique_member_fullname",
                violation_error_message="Ein Mitglied mit diesem Namen und Nachnamen existiert bereits.",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.surname}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("middle", "Middle"),
        ("high", "High"),
    ]

    task = models.CharField(
        "Aufgabe",
        max_length=127,
        unique=True,
        error_messages={"unique": "Eine Aufgabe mit diesem Namen existiert bereits."},
    )
    description = models.TextField(
        "Beschreibung",
        blank=True,
        null=True,
        max_length=255,
    )
    priority = models.CharField(
        max_length=7, choices=PRIORITY_CHOICES, default="middle"
    )
    finished = models.BooleanField("Erledigt", default=False)
    moved_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.pk:
            old_status = Task.objects.get(pk=self.pk).finished
            if old_status != self.finished:
                self.moved_at = timezone.now()
        else:
            self.moved_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.task
