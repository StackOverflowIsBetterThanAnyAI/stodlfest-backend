from django.db import models


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

    def __str__(self):
        return self.task
