import base64
import json
import os
from pathlib import Path

from uuid import uuid4

from app.ingestion.models import (
    DocumentElement,
    SourceLocation,
)

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class VisionExtractor:

    def __init__(self):
        self.client = Groq(
            api_key=os.environ["GROQ_API_KEY"]
        )

    def extract(
        self,
        image_path: Path,
        query: str,
        page_number: int,
    ):

        image_base64 = self._encode_image(image_path)

        prompt = f"""
Analyze the document page and answer the user's question using only
information visible in the image.

Question:
{query}

Return valid JSON:
{{
  "source": "...",
  "answer": "...",
  "evidence": "..."
}}

Rules:
- Inspect the entire page and identify the relevant chart, table, or figure.
- Match the exact indicator, category, or label asked about.
- Read the value explicitly displayed for that indicator.
- Do not use values from neighboring or unrelated elements.
- Prefer displayed values over visual estimation.
- Verify that the value belongs to the requested indicator.
- Preserve the exact value and unit.
- Do not guess or calculate. If the value is not reliably visible, return null for "answer".
- Use the relevant visual's visible title as "source" when available.
- Return only the requested information.
"""
        
        response = self.client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:image/png;base64,"
                                    f"{image_base64}"
                                )
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_completion_tokens=500,
            response_format={"type": "json_object"},
        )

        return json.loads(
            response.choices[0].message.content
        )

    def to_elements(
        self,
        result: dict,
        source_file: str,
        document_id: str,
        page_number: int,
        start_order: int,
    ) -> tuple[list[DocumentElement], int]:

        elements = []
        order = start_order

        for item in result.get("elements", []):

            element_type = item.get("type", "other")

            text_parts = []

            title = item.get("title")
            content = item.get("content")

            if title:
                text_parts.append(title)

            if content:
                text_parts.append(content)

            if item.get("x_axis"):
                text_parts.append(
                    f"X-axis: {item['x_axis']}"
                )

            if item.get("y_axis"):
                text_parts.append(
                    f"Y-axis: {item['y_axis']}"
                )

            observations = item.get("observations", [])

            if observations:
                text_parts.append(
                    "Observations: "
                    + " ".join(observations)
                )

            text = "\n".join(text_parts).strip()

            if not text:
                continue

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    text=text,
                    element_type=element_type,
                    source_file=source_file,
                    order=order,
                    location=SourceLocation(
                        page=page_number
                    ),
                    metadata={
                        "document_id": document_id,
                        "parser": "vision_llm",
                        "chart_type": item.get("chart_type"),
                        "series": item.get("series", []),
                        "sample_sizes": item.get(
                            "sample_sizes", []
                        ),
                    },
                )
            )

            order += 1

        return elements, order

    @staticmethod
    def _encode_image(image_path: Path) -> str:

        with image_path.open("rb") as image_file:
            return base64.b64encode(
                image_file.read()
            ).decode("utf-8")