
import ollama


class LLMService:
    """Connect the healthcare testing framework to a local Ollama model."""

    def __init__(self, model: str = "llama3.2:latest"):
        self.model = model

    def generate_response(self, prompt: str) -> str:
        """Generate a response from the local language model."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"].strip()
