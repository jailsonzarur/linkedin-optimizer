from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from knowledge.models import Conversation, Message
from knowledge.services.conversation import CLOSING_MARKER, extract, split_closing, stream_question
from knowledge.services.finalise import finalise
from knowledge.tasks import transcribe_message


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related("messages"), pk=pk, user=request.user
    )
    messages = list(conversation.messages.all())
    return render(
        request,
        "knowledge/conversation.html",
        {
            "conversation": conversation,
            "messages": messages,
            "awaiting": bool(messages) and messages[-1].role == Message.Role.USER,
        },
    )


@login_required
@require_POST
def conversation_reply(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    content = (request.POST.get("content") or "").strip()

    if not content:
        return HttpResponse(status=204)

    message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=content,
        status=Message.Status.DONE,
    )
    return render(request, "knowledge/partials/_reply_posted.html",
                  {"conversation": conversation, "message": message})


def _frame(event, payload):
    body = "".join(f"data: {line}\n" for line in payload.split("\n") or [""])
    return f"event: {event}\n{body}\n"


async def conversation_stream(request, pk):
    user = await request.auser()
    if not user.is_authenticated:
        raise Http404

    conversation = await Conversation.objects.filter(pk=pk, user=user).afirst()
    if conversation is None:
        raise Http404

    async def turn():
        messages = await sync_to_async(list)(conversation.messages.all())
        if not messages or messages[-1].role != Message.Role.USER:
            yield _frame("done", "")
            return

        yield _frame("thinking", "")
        conversation.record = await extract(conversation.record, messages)
        await conversation.asave(update_fields=["record", "updated_at"])

        confirmed = (conversation.record.get("closing") or {}).get("user_confirmed")
        if confirmed and len(messages) > 2:
            analysis = await sync_to_async(finalise)(conversation)
            yield _frame("finalised", str(analysis.pk))
            yield _frame("done", "")
            return

        yield _frame("typing", "")

        collected = []
        closing = False
        streaming = True
        try:
            async for token in stream_question(conversation.record, messages):
                collected.append(token)
                if "[" in token:
                    streaming = False
                if streaming:
                    yield _frame("token", token.replace("\n", " "))
        finally:
            text, closing = split_closing("".join(collected).strip())
            if text:
                await Message.objects.acreate(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=text,
                    status=Message.Status.DONE,
                )

        html = await sync_to_async(render_to_string)(
            "knowledge/partials/_message.html",
            {"message": {"role": "assistant", "content": text}},
        )
        yield _frame("settled", html.replace("\n", ""))
        yield _frame("closing", "1" if closing else "")
        yield _frame("done", "")

    response = StreamingHttpResponse(turn(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@login_required
@require_POST
def conversation_answer_audio(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    upload = request.FILES.get("audio")
    if not upload:
        return HttpResponse(status=400)

    message = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        audio_file=upload,
        status=Message.Status.PENDING,
    )
    transaction.on_commit(lambda: transcribe_message.delay(message.pk))
    return render(request, "knowledge/partials/_message_pending.html", {"message": message})


@login_required
def message_status(request, pk):
    message = get_object_or_404(Message, pk=pk, conversation__user=request.user)
    if message.status == Message.Status.DONE:
        return render(request, "knowledge/partials/_message_settled.html", {"message": message})
    return render(request, "knowledge/partials/_message_pending.html", {"message": message})


@login_required
@require_POST
def conversation_finish(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    analysis = finalise(conversation)
    return redirect("analysis:running", pk=analysis.pk)
