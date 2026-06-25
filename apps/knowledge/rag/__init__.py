from openai import OpenAI
from django.conf import settings


def get_llm_client() -> OpenAI:
    """Get an OpenAI-compatible client pointed at SiliconFlow."""
    return OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
    )
