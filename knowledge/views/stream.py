import asyncio
import json

import redis.asyncio as aioredis
from django.conf import settings
from django.http import StreamingHttpResponse
from django.template.loader import render_to_string

from knowledge.models import ProfileImport
from knowledge.services.events import channel, log_key

STEP_LABELS = {
    "extract.started": "Opening your files",
    "extract.profile": "Read your LinkedIn profile",
    "extract.resume": "Read your résumé",
    "extract.resume_skipped": "Could not read the résumé — carrying on without it",
    "judge.started": "Reading what is there",
    "judge.parsed": "Found your experiences",
    "judge.progress": "Looking at each role",
    "judge.sections": "Checking headline, About and skills",
    "judge.done": "Analysis finished",
    "conversation.ready": "Getting your first question ready",
}

HEARTBEAT_SECONDS = 15


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


async def onboarding_stream(request, pk):
    user = await request.auser()
    if not user.is_authenticated:
        return StreamingHttpResponse(_frame("failed", "Not signed in."),
                                     content_type="text/event-stream", status=403)

    if not await ProfileImport.objects.filter(pk=pk, user=user).aexists():
        return StreamingHttpResponse(_frame("failed", "Not found."),
                                     content_type="text/event-stream", status=404)

    async def events():
        client = aioredis.from_url(settings.CELERY_BROKER_URL)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel(pk))

        try:
            for raw in await client.lrange(log_key(pk), 0, -1):
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
            await pubsub.unsubscribe(channel(pk))
            await pubsub.aclose()
            await client.aclose()

    response = StreamingHttpResponse(events(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
