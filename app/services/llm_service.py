import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def generate(self, query: str, context: str) -> str:

        print("\n========== LLM GENERATION ==========")
        print("Model:", self.model)
        print("Query:", query)
        print("Context characters:", len(context))

        system_prompt = """
You are a document question-answering assistant.

Answer the user's question using only the provided document context.

Rules:
- Do not use outside knowledge.
- If the answer is not present in the context, say that the information is not available in the provided documents.
- Be precise and concise.
- Preserve important numbers, names, dates, and units.
"""

        user_prompt = f"""
Document context:

{context}

User question:
{query}

Answer:
"""

        print(">>> CALLING GPT-OSS")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.1,
            max_tokens=800,
        )

        answer = response.choices[0].message.content

        print(">>> GPT-OSS RESPONSE RECEIVED")
        print("Answer:", answer)
        print("===================================\n")

        return answer