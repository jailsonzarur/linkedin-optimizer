from django.conf import settings

from knowledge.services.openai_client import get_client


class Embedder:
    BATCH_SIZE = 96

    def __init__(self, client=None, model=None):
        self._client = client
        self.model = model or settings.OPENAI_EMBEDDING_MODEL

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def embed(self, texts):
        vectors = []
        for start in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[start : start + self.BATCH_SIZE]
            response = self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in sorted(response.data, key=lambda d: d.index))
        return vectors
