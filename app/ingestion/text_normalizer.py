import re


class TextNormalizer:

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(
            r"(?<!\n)\n(?!\n)",
            " ",
            text,
        )

        text = re.sub(
            r" +([,.;:!?])",
            r"\1",
            text,
        )

        text = re.sub(
            r"([(\[])\s+",
            r"\1",
            text,
        )

        text = re.sub(
            r"\s+([)\]])",
            r"\1",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()