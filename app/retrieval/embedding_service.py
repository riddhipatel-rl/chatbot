from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        self.model = None

    def _load_model(self):

        if self.model is None:
            print("Loading BGE model...")

            self.model = SentenceTransformer(
                "BAAI/bge-small-en-v1.5"
            )

    def embed(self, texts):

        self._load_model()

        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )