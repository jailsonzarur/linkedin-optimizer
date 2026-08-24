from django.conf import settings
from openai import AsyncOpenAI, OpenAI


class MissingCredentials(RuntimeError):
    pass


def _key():
    if not settings.OPENAI_API_KEY:
        raise MissingCredentials("OPENAI_API_KEY is not set.")
    return settings.OPENAI_API_KEY


def get_client():
    return OpenAI(api_key=_key())


def get_async_client():
    return AsyncOpenAI(api_key=_key())
