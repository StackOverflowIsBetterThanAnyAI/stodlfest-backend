from django.db import models


class Member(models.Model):
    AGE_CHOICES = [
        ("underage", "Underage"),
        ("ofLegalAge", "Of Legal Age"),
    ]

    name = models.CharField("Name", max_length=63)
    surname = models.CharField("Nachname", max_length=63)
    age = models.CharField("Alter", max_length=15, choices=AGE_CHOICES)

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
