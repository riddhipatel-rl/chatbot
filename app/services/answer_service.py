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
- Answer the user's question directly using only the provided document context.
- Do not use outside knowledge or invent information.
- Select the answer format based on the question and content.
- For questions asking for multiple items, start with a short introductory sentence and present each item as a separate Markdown bullet.
- For step-by-step processes, use a numbered list.
- For comparisons, use a Markdown table when it makes the information easier to understand.
- For simple factual questions, use one or two natural sentences.
- For longer or multi-part answers, use short paragraphs and meaningful headings where helpful.
- Put each distinct idea on a separate line or paragraph when it improves readability.
- Use Markdown bold for important terms, values, or conclusions, but do not bold entire paragraphs.
- Avoid unnecessary headings, repeated information, and overly long explanations.
- Keep the answer concise without combining unrelated points into one long sentence.
- Identify the single source that most directly supports the answer.
- Return the index of that single SOURCE.
- Do not include file names or page numbers in the answer; the application provides source information separately.

Return valid JSON with these two fields:
{{
    "answer": "The six service areas are:\\n- **Antenatal care**\\n- **HIV testing and counselling**\\n- **Antiretroviral therapy**\\n- **Preventing mother-to-child transmission of HIV (PMTCT)**\\n- **Malaria**\\n- **Tuberculosis**",
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