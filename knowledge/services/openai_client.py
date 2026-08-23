from django.conf import settings
from openai import OpenAI


class MissingCredentials(RuntimeError):
    pass


def get_client():
    if not settings.OPENAI_API_KEY:
        raise MissingCredentials("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=settings.OPENAI_API_KEY)
