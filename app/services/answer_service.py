import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class AnswerService:

    def __init__(self):
        self.retrieval_service = None

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model = "openai/gpt-oss-120b"

    def answer(
        self,
        query: str,
        top_k: int = 2,
    ):

        results = self.retrieval_service.search(
            query=query,
            top_k=top_k,
        )

        if not results:
            return {
                "answer": (
                    "I could not find relevant information "
                    "in the uploaded documents."
                ),
                "sources": [],
            }

        context = self._build_context(
            results
        )

        prompt = f"""
Answer the user's question using only the provided document context.

Question:
{query}

Document context:
{context}

Rules:
- Use only the provided document context.
- Do not use outside knowledge.
- Do not invent information.
- Identify the source that directly supports the answer.
- The answer must be a complete natural-language sentence.
- Never return only a number, percentage, date, or short phrase.
- Bold the key answer or value using Markdown **bold**.
- Keep the answer concise.
- Return the index of the single SOURCE that directly supports the answer.
- Do not return multiple source indexes.
- Do not generate file names or page numbers.
- The application will provide the source and page information.

Return valid JSON:

{{
    "answer": "The percentage of patients experiencing the secondary composite CV outcome in the Kerendia group was **13.0%**.",
    "source_index": 1
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
            max_completion_tokens=700,
            response_format={
                "type": "json_object"
            },
        )

        generated = json.loads(
            response.choices[0].message.content
        )

        source_index = self._validate_source_index(
            generated.get("source_index"),
            len(results),
        )

        selected_result = results[
            source_index - 1
        ]

        return {
            "answer": generated.get(
                "answer",
                "",
            ),
            "sources": [
                self._build_source(
                    selected_result
                )
            ],
        }

    def _build_context(self, results):

        context = []

        for index, result in enumerate(
            results,
            start=1,
        ):

            chunk = result["chunk"]

            pages = sorted(
                {
                    location.page
                    for location in chunk.locations
                    if location.page is not None
                }
            )

            context.append(
                f"""
SOURCE {index}

File:
{chunk.source_file}

Pages:
{pages}

Text:
{chunk.text}
"""
            )

            visual_evidence = result.get(
                "visual_evidence",
                [],
            )

            if visual_evidence:

                context.append(
                    f"""
VISUAL EVIDENCE {index}:

{json.dumps(
    visual_evidence,
    ensure_ascii=False,
)}
"""
                )

        return "\n".join(context)

    def _build_source(self, result):

        chunk = result["chunk"]

        pages = sorted(
            {
                location.page
                for location in chunk.locations
                if location.page is not None
            }
        )

        return {
            "file": chunk.source_file,
            "pages": pages,
            "evidence": self._build_evidence(
                result
            ),
        }

    def _build_evidence(self, result):

        chunk = result["chunk"]

        evidence = []

        visual_evidence = result.get(
            "visual_evidence",
            [],
        )

        # Qwen-generated visual evidence only.
        for visual in visual_evidence:

            visual_result = visual.get(
                "visual_result",
                {},
            )

            title = (
                visual_result.get("source")
                or visual_result.get("title")
            )

            evidence_text = (
                visual_result.get("evidence")
                or visual_result.get("answer")
            )

            if not title and not evidence_text:
                continue

            evidence.append(
                {
                    "type": "vision",
                    "page": visual.get("page"),
                    "title": title,
                    "evidence": evidence_text,
                }
            )

        # Native/extractable visual content.
        if chunk.metadata.get(
            "visual_page"
        ):

            visual_elements = (
                chunk.metadata.get(
                    "visual_elements",
                    [],
                )
            )

            if visual_elements:

                for visual in visual_elements:

                    evidence.append(
                        {
                            "type": "visual_text",
                            "page": visual.get(
                                "page"
                            ),
                            "title": visual.get(
                                "title"
                            ),
                            "evidence": visual.get(
                                "text"
                            ),
                        }
                    )

            elif not visual_evidence:

                evidence.append(
                    {
                        "type": "visual_text",
                        "page": self._get_first_page(
                            chunk
                        ),
                        "title": self._extract_visual_title(
                            chunk.text
                        ),
                        "evidence": chunk.text,
                    }
                )

        return evidence

    @staticmethod
    def _extract_visual_title(
        text: str,
    ):

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:

            lower = line.lower()

            if (
                lower.startswith("fig.")
                or lower.startswith("fig ")
                or lower.startswith("figure ")
                or lower.startswith("table ")
                or lower.startswith("chart ")
            ):
                return line

        return None

    @staticmethod
    def _get_first_page(chunk):

        pages = [
            location.page
            for location in chunk.locations
            if location.page is not None
        ]

        return min(pages) if pages else None

    @staticmethod
    def _validate_source_index(
        source_index,
        result_count,
    ):

        try:
            source_index = int(
                source_index
            )
        except (
            TypeError,
            ValueError,
        ):
            return 1

        if not 1 <= source_index <= result_count:
            return 1

        return source_index