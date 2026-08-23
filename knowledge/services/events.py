import json

import redis
from django.conf import settings

STREAM_TTL_SECONDS = 60 * 60


def _client():
    return redis.Redis.from_url(settings.CELERY_BROKER_URL)


def channel(import_id):
    return f"onboarding:{import_id}"


def log_key(import_id):
    return f"onboarding:{import_id}:log"


def publish(import_id, name, detail=""):
    payload = json.dumps({"name": name, "detail": str(detail)})
    client = _client()
    pipe = client.pipeline()
    pipe.rpush(log_key(import_id), payload)
    pipe.expire(log_key(import_id), STREAM_TTL_SECONDS)
    pipe.publish(channel(import_id), payload)
    pipe.execute()


def history(import_id):
    client = _client()
    return [json.loads(raw) for raw in client.lrange(log_key(import_id), 0, -1)]
