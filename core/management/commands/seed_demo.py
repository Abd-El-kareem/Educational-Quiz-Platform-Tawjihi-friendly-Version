from django.core.management.base import BaseCommand

from catalog.models import Category
from quizzes.services import create_quiz
from scoring.models import Score


class Command(BaseCommand):
    help = "Seed sample categories and quizzes for local development."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        science, _ = Category.objects.get_or_create(name="Science")
        history, _ = Category.objects.get_or_create(name="History")

        create_quiz(
            created_by=None,
            title="General Science Basics",
            category=Category.objects.get(pk=science.pk),
            is_public=True,
            access_code=None,
            questions=[
                {
                    "text": "What planet is known as the Red Planet?",
                    "points": 10,
                    "answers": [
                        {"text": "Mars", "is_correct": True},
                        {"text": "Venus", "is_correct": False},
                        {"text": "Jupiter", "is_correct": False},
                    ],
                },
                {
                    "text": "H2O is the chemical formula for...",
                    "points": 10,
                    "answers": [
                        {"text": "Water", "is_correct": True},
                        {"text": "Salt", "is_correct": False},
                        {"text": "Oxygen", "is_correct": False},
                    ],
                },
                {
                    "text": "Which of these is a renewable energy source?",
                    "points": 20,
                    "answers": [
                        {"text": "Solar", "is_correct": True},
                        {"text": "Coal", "is_correct": False},
                    ],
                },
            ],
        )
        self.stdout.write("  + Quiz: General Science Basics (public)")

        create_quiz(
            created_by=None,
            title="Ancient Civilizations",
            category=Category.objects.get(pk=history.pk),
            is_public=True,
            access_code=None,
            questions=[
                {
                    "text": "Which empire built the Colosseum?",
                    "points": 10,
                    "answers": [
                        {"text": "Roman", "is_correct": True},
                        {"text": "Greek", "is_correct": False},
                        {"text": "Egyptian", "is_correct": False},
                    ],
                },
                {
                    "text": "The Great Pyramid of Giza was built in which country?",
                    "points": 10,
                    "answers": [
                        {"text": "Egypt", "is_correct": True},
                        {"text": "Mexico", "is_correct": False},
                    ],
                },
            ],
        )
        self.stdout.write("  + Quiz: Ancient Civilizations (public)")

        create_quiz(
            created_by=None,
            title="Space Trivia (Private)",
            category=Category.objects.get(pk=science.pk),
            is_public=False,
            access_code="SPACE42",
            questions=[
                {
                    "text": "How many moons does Mars have?",
                    "points": 10,
                    "answers": [
                        {"text": "2", "is_correct": True},
                        {"text": "1", "is_correct": False},
                        {"text": "0", "is_correct": False},
                    ],
                },
            ],
        )
        self.stdout.write("  + Quiz: Space Trivia (private, code SPACE42)")

        create_quiz(
            created_by=None,
            title="Math & Physics Basics",
            category=Category.objects.get(pk=science.pk),
            is_public=True,
            access_code=None,
            questions=[
                {
                    "text": "What is the famous equation relating energy and mass?",
                    "points": 10,
                    "math_enabled": True,
                    "answers": [
                        {"text": r"$E = mc^2$", "is_correct": True},
                        {"text": r"$E = \frac{m}{c^2}$", "is_correct": False},
                        {"text": r"$F = ma$", "is_correct": False},
                    ],
                },
                {
                    "text": "Solve for $x$:  $x^2 - 5x + 6 = 0$",
                    "points": 20,
                    "math_enabled": True,
                    "answers": [
                        {"text": r"$x = 2$ or $x = 3$", "is_correct": True},
                        {"text": r"$x = -2$ or $x = -3$", "is_correct": False},
                        {"text": r"$x = \pm \sqrt{5}$", "is_correct": False},
                    ],
                },
                {
                    "text": "Newton's second law states:",
                    "points": 10,
                    "math_enabled": True,
                    "answers": [
                        {"text": r"$\vec{F} = m\vec{a}$", "is_correct": True},
                        {"text": r"$\vec{F} = m\vec{v}$", "is_correct": False},
                        {"text": r"$\vec{F} = \frac{d\vec{p}}{dt}$", "is_correct": False},
                    ],
                },
                {
                    "text": "Which of these equals the derivative of $x^3$?",
                    "points": 20,
                    "math_enabled": True,
                    "answers": [
                        {"text": r"$3x^2$", "is_correct": True},
                        {"text": r"$\frac{1}{4}x^4 + C$", "is_correct": False},
                        {"text": r"$x^2$", "is_correct": False},
                    ],
                },
            ],
        )
        self.stdout.write("  + Quiz: Math & Physics Basics (LaTeX, public)")

        Score.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Done. Categories: Science, History. Quizzes: 3."))
