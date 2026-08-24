import logging

from celery import shared_task
from django.db import transaction

from analysis.models import Analysis, AnalysisSection
from analysis.services.rewriter import ProfileRewriter
from knowledge.services.events import publish

logger = logging.getLogger(__name__)
PREFIX = "analysis"


@shared_task
def analyse_profile(analysis_id):
    analysis = Analysis.objects.select_related("profile_import").get(pk=analysis_id)
    conversation = analysis.profile_import.conversations.first()
    record = conversation.record if conversation else analysis.profile_import.judgment

    analysis.status = Analysis.Status.RUNNING
    analysis.save(update_fields=["status"])
    publish(analysis_id, "analysis.started", "", prefix=PREFIX)

    emit = lambda name, detail: publish(analysis_id, name, detail, prefix=PREFIX)
    rewriter = ProfileRewriter(record, on_event=emit)
    rows = []

    try:
        original, variants = rewriter.headline()
        rows += [
            AnalysisSection(
                analysis=analysis,
                section=AnalysisSection.Section.HEADLINE,
                original_text=original,
                suggested_text=variant,
                variant_index=index,
            )
            for index, variant in enumerate(variants)
        ]

        original, text = rewriter.about()
        if text:
            rows.append(AnalysisSection(
                analysis=analysis,
                section=AnalysisSection.Section.ABOUT,
                original_text=original,
                suggested_text=text,
            ))

        for experience, lines in rewriter.experiences():
            rows += [
                AnalysisSection(
                    analysis=analysis,
                    section=AnalysisSection.Section.EXPERIENCE_BULLET,
                    source_ref=experience.get("id", ""),
                    original_text=experience.get("content", ""),
                    suggested_text=line,
                    variant_index=index,
                )
                for index, line in enumerate(lines)
            ]

        overall, per_section = rewriter.scores()
    except Exception:
        logger.exception("Rewrite failed for analysis %s", analysis_id)
        analysis.status = Analysis.Status.FAILED
        analysis.save(update_fields=["status"])
        publish(analysis_id, "failed", "Something went wrong writing the rewrite.", prefix=PREFIX)
        return

    with transaction.atomic():
        analysis.sections.all().delete()
        AnalysisSection.objects.bulk_create(rows)
        analysis.overall_score = overall
        analysis.overall_score_per_section = per_section
        analysis.status = Analysis.Status.DONE
        analysis.save(update_fields=["overall_score", "overall_score_per_section", "status"])

    publish(analysis_id, "done", analysis_id, prefix=PREFIX)
