from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analysis.models import Analysis, AnalysisSection
from knowledge.models import ProfileImport

HEADLINE_ORIGINAL = "Developer at TechCorp"
HEADLINE_VARIANTS = [
    "Backend Developer · Python, Django and PostgreSQL · High-scale APIs",
    "Backend Software Engineer · Django, Docker, AWS · Distributed systems",
    "Backend Developer @ TechCorp · Python · API scalability and performance",
]

ABOUT_ORIGINAL = (
    "I am a developer passionate about technology, always looking to learn new things. "
    "I have experience with web development and I enjoy working in a team. "
    "I currently work at TechCorp, on the platform team."
)
ABOUT_SUGGESTED = (
    "I am a developer passionate about technology, always looking to learn new things. "
    "For 5 years I have built REST APIs in Python and Django that sustain peaks of "
    "40k requests per minute, focused on performance and observability. "
    "I currently work at TechCorp, on the platform team."
)

BULLETS = [
    (
        "Responsible for API development.",
        "Built 12 REST APIs in Django sustaining 40k req/min, cutting p95 latency by 38%.",
    ),
    (
        "Took part in the legacy system migration.",
        "Led the migration of a PHP monolith to Dockerised Django services with zero downtime over 7 months.",
    ),
    (
        "Ran code reviews and mentored interns.",
        "Ran code reviews and mentored interns.",
    ),
]

KEYWORD_GAP = [
    {"term": "Docker", "coverage": 87, "present": False, "supported": True},
    {"term": "PostgreSQL", "coverage": 68, "present": True, "supported": True},
    {"term": "Kubernetes", "coverage": 51, "present": False, "supported": False},
    {"term": "CI/CD", "coverage": 46, "present": False, "supported": True},
]


class Command(BaseCommand):
    help = "Seed a demo Analysis for developing the result screen."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="rafael.demo",
            help="Attach the demo analysis to this account instead of the default demo user.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if username != "rafael.demo":
                raise CommandError(
                    f"No account named {username!r}. Create it through the signup page first."
                )
            user = User.objects.create(
                username=username,
                first_name="Rafael",
                last_name="Moreira",
                email="rafael@example.com",
            )

        snapshot = ProfileSnapshot.objects.create(
            user=user,
            raw_content="\n\n".join([HEADLINE_ORIGINAL, ABOUT_ORIGINAL, *[b[0] for b in BULLETS]]),
        )

        analysis = Analysis.objects.create(
            user=user,
            profile_import=imported,
            overall_score=68,
            overall_score_per_section={
                "headline": 45,
                "about": 72,
                "experience_bullet": 81,
                "keywords": 38,
            },
            keyword_gap=KEYWORD_GAP,
            status=Analysis.Status.DONE,
        )

        for index, suggested in enumerate(HEADLINE_VARIANTS):
            AnalysisSection.objects.create(
                analysis=analysis,
                section=AnalysisSection.Section.HEADLINE,
                original_text=HEADLINE_ORIGINAL,
                suggested_text=suggested,
                variant_index=index,
            )

        AnalysisSection.objects.create(
            analysis=analysis,
            section=AnalysisSection.Section.ABOUT,
            original_text=ABOUT_ORIGINAL,
            suggested_text=ABOUT_SUGGESTED,
            variant_index=0,
        )

        for original, suggested in BULLETS:
            AnalysisSection.objects.create(
                analysis=analysis,
                section=AnalysisSection.Section.EXPERIENCE_BULLET,
                original_text=original,
                suggested_text=suggested,
                variant_index=0,
            )

        self.stdout.write(self.style.SUCCESS(f"Analysis #{analysis.pk} created for {user.username} at /analysis/{analysis.pk}/"))
