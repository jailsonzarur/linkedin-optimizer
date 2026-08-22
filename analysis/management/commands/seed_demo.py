from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from analysis.models import Analysis, AnalysisSection, ProfileSnapshot

HEADLINE_ORIGINAL = "Desenvolvedor na TechCorp"
HEADLINE_VARIANTS = [
    "Backend Developer · Python, Django e PostgreSQL · APIs de alta escala",
    "Engenheiro de Software Backend · Django, Docker, AWS · Sistemas distribuídos",
    "Backend Developer @ TechCorp · Python · Escalabilidade e performance de APIs",
]

ABOUT_ORIGINAL = (
    "Sou desenvolvedor apaixonado por tecnologia, sempre buscando aprender coisas novas. "
    "Tenho experiência com desenvolvimento web e gosto de trabalhar em equipe. "
    "Atualmente trabalho na TechCorp, onde atuo no time de plataforma."
)
ABOUT_SUGGESTED = (
    "Sou desenvolvedor apaixonado por tecnologia, sempre buscando aprender coisas novas. "
    "Trabalho há 5 anos com Python e Django construindo APIs REST que sustentam picos de "
    "40 mil requisições por minuto, com foco em performance e observabilidade. "
    "Atualmente trabalho na TechCorp, onde atuo no time de plataforma."
)

BULLETS = [
    (
        "Responsável pelo desenvolvimento de APIs.",
        "Desenvolvi 12 APIs REST em Django que sustentam 40k req/min, reduzindo a latência p95 em 38%.",
    ),
    (
        "Participei da migração do sistema legado.",
        "Liderei a migração de um monolito PHP para serviços Django em Docker, sem downtime, ao longo de 7 meses.",
    ),
    (
        "Atuei em code review e mentoria de estagiários.",
        "Atuei em code review e mentoria de estagiários.",
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

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="rafael.demo",
            defaults={"first_name": "Rafael", "last_name": "Moreira", "email": "rafael@example.com"},
        )

        snapshot = ProfileSnapshot.objects.create(
            user=user,
            raw_content="\n\n".join([HEADLINE_ORIGINAL, ABOUT_ORIGINAL, *[b[0] for b in BULLETS]]),
        )

        analysis = Analysis.objects.create(
            user=user,
            profile_snapshot=snapshot,
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

        self.stdout.write(self.style.SUCCESS(f"Analysis #{analysis.pk} created at /analise/{analysis.pk}/"))
