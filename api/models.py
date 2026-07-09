from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Job(models.Model):
    job = models.CharField(
        "Arbeit",
        max_length=63,
        unique=True,
        error_messages={"unique": "Eine Arbeit mit diesem Namen existiert bereits."},
    )
    workers = models.PositiveIntegerField(
        "Helfer",
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        error_messages={
            "min_value": "Es muss mindestens 1 Helfer zugewiesen werden.",
            "max_value": "Es dürfen maximal 15 Helfer zugewiesen werden.",
        },
    )

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
    job = models.CharField("Beruf", max_length=63, blank=True, null=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField("Erledigt", default=False)

    def __str__(self):
        return self.task
