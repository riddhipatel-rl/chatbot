from sentence_transformers import CrossEncoder

class Reranker:

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model_name = model_name
        self.model = None

    def _load_model(self):

        if self.model is None:
            print("Loading reranker model...")

            self.model = CrossEncoder(
                self.model_name
            )

    def rerank(
        self,
        query,
        candidates,
        top_k=5,
    ):

        if not candidates:
            return []

        self._load_model()

        pairs = [
            (
                query,
                candidate["chunk"].text,
            )
            for candidate in candidates
        ]

        scores = self.model.predict(pairs)

        for candidate, score in zip(
            candidates,
            scores,
        ):
            candidate["rerank_score"] = float(
                score
            )

        candidates.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return candidates[:top_k]