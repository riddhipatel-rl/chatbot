from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleRetriever:

    def __init__(self, elements: list[dict]):
        self.elements = elements

        self.vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        self.vectors = self.vectorizer.fit_transform(
            [element["text"] for element in elements]
        )

    def search(self, query: str, k: int = 5) -> list[dict]:
        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.vectors,
        )[0]

        ranked_indices = scores.argsort()[::-1][:k]

        results = []

        for index in ranked_indices:
            result = self.elements[index].copy()
            result["score"] = float(scores[index])
            results.append(result)

        return results