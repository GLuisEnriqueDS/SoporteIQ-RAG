import os

from google import genai
from google.genai import types

from . import config

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.VERTEX_CREDENTIALS_JSON
        _client = genai.Client(
            vertexai=True,
            project=config.VERTEX_PROJECT_ID,
            location=config.VERTEX_LOCATION,
        )
    return _client


def generate(prompt: str, temperature: float = 0.2) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature, max_output_tokens=1024),
    )
    return (response.text or "").strip()
