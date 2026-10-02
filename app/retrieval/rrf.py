class RRFFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        ranked_lists: list[list[str]],
        top_k: int = 5,
    ) -> list[tuple[str, float]]:

        scores = {}

        for ranked_list in ranked_lists:
            for rank, chunk_id in enumerate(
                ranked_list,
                start=1,
            ):
                scores[chunk_id] = (
                    scores.get(chunk_id, 0.0)
                    + 1.0 / (self.k + rank)
                )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked[:top_k]