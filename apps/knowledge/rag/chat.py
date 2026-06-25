"""
Streaming chat with RAG — retrieve context → build prompt → stream LLM reply.
"""

import json
from typing import Generator

from django.conf import settings
from django.http import StreamingHttpResponse

from . import get_llm_client
from .engine import retrieve

SYSTEM_PROMPT = """你是一个知识库问答助手。请严格基于用户提供的文档内容回答问题。

规则：
1. 只使用下面提供的「参考文档」中的信息来回答。
2. 如果参考文档中没有相关信息，请诚实地说"文档中没有找到相关信息"。
3. 回答时引用具体的文档片段，标注出处文件名。
4. 用简体中文回答，清晰有条理。
5. 使用 Markdown 格式组织回答（标题、列表、加粗等）。
"""


def build_context(sources: list[dict]) -> str:
    """Build a context string from retrieved sources."""
    parts = []
    for i, s in enumerate(sources, 1):
        parts.append(
            f"[{i}] 来源：{s['filename']}（片段{s['chunk_index'] + 1}）\n"
            f"{s['content']}"
        )
    return "\n\n".join(parts)


def stream_rag_response(
    user_message: str,
    sources: list[dict],
) -> Generator[str, None, None]:
    """Stream the LLM response chunk by chunk, yielding SSE events."""

    if not sources:
        yield f"data: {json.dumps({'type': 'text', 'content': '知识库中没有相关文档，无法回答该问题。请先上传一些文档。'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    context = build_context(sources)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"参考文档：\n\n{context}\n\n---\n\n用户问题：{user_message}",
        },
    ]

    client = get_llm_client()

    try:
        stream = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            stream=True,
        )

        full_content = []
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content.append(content)
                yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"

        # Send sources at the end
        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


def create_sse_response(
    user_message: str,
    sources: list[dict],
) -> StreamingHttpResponse:
    """Build a Django HTTP response for SSE streaming."""
    response = StreamingHttpResponse(
        stream_rag_response(user_message, sources),
        content_type="text/event-stream",
        status=200,
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
