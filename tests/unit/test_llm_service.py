
from unittest.mock import patch

import pytest

from src.services.llm_service import LLMService


def test_llm_service_returns_generated_response():
    service = LLMService()

    fake_response = {
        "message": {
            "content": "Healthcare AI is ready."
        }
    }

    with patch("src.services.llm_service.ollama.chat", return_value=fake_response):
        result = service.generate_response("Explain healthcare AI testing.")

    assert result == "Healthcare AI is ready."


def test_llm_service_rejects_empty_prompt():
    service = LLMService()

    with pytest.raises(ValueError, match="non-empty string"):
        service.generate_response("")


def test_llm_service_rejects_whitespace_prompt():
    service = LLMService()

    with pytest.raises(ValueError, match="non-empty string"):
        service.generate_response("   ")
