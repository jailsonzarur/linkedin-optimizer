import asyncio
import json

import redis.asyncio as aioredis
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from analysis.models import Analysis
from knowledge.services.events import channel, log_key

PREFIX = "analysis"
HEARTBEAT_SECONDS = 15

STEP_LABELS = {
    "analysis.started": "Reading everything you told us",
    "analysis.headline": "Writing your headline",
    "analysis.about": "Writing your About section",
    "analysis.experience": "Rewriting your experience",
    "analysis.scoring": "Scoring what you have today",
}


def _frame(event, html):
    body = "".join(f"data: {line}\n" for line in html.splitlines() or [""])
    return f"event: {event}\n{body}\n"


def _render(name, detail):
    label = STEP_LABELS.get(name, name)
    return {
        "step": render_to_string("knowledge/partials/_stream_step.html",
                                 {"label": label, "detail": detail, "name": name}),
        "log": render_to_string("knowledge/partials/_stream_log.html",
                                {"label": label, "detail": detail, "name": name}),
    }


@login_required
def analysis_running(request, pk):
    analysis = get_object_or_404(Analysis, pk=pk, user=request.user)
    if analysis.status == Analysis.Status.DONE:
        return redirect("analysis:result", pk=pk)
    return render(request, "analysis/running.html", {"analysis": analysis})


async def analysis_stream(request, pk):
    user = await request.auser()
    if not user.is_authenticated:
        raise Http404
    if not await Analysis.objects.filter(pk=pk, user=user).aexists():
        raise Http404

    async def events():
        client = aioredis.from_url(settings.CELERY_BROKER_URL)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel(pk, PREFIX))

        try:
            for raw in await client.lrange(log_key(pk, PREFIX), 0, -1):
                event = json.loads(raw)
                for kind, html in _render(event["name"], event["detail"]).items():
                    yield _frame(kind, html)
                if event["name"] in ("done", "failed"):
                    yield _frame(event["name"], event["detail"])
                    return

            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=HEARTBEAT_SECONDS,
                    )
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                if not message:
                    continue

                event = json.loads(message["data"])
                for kind, html in _render(event["name"], event["detail"]).items():
                    yield _frame(kind, html)
                if event["name"] in ("done", "failed"):
                    yield _frame(event["name"], event["detail"])
                    return
        finally:
            await pubsub.unsubscribe(channel(pk, PREFIX))
            await pubsub.aclose()
            await client.aclose()

    response = StreamingHttpResponse(events(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
