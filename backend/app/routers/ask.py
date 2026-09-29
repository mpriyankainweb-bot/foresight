import asyncio
import json
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models import AskRequest

router = APIRouter(prefix="/api/v1", tags=["ask"])

memory_service = MemoryService()
llm_client = LLMClient()


def synthesize_answer_from_memories(question: str, memories: list[dict]) -> str:
    """
    Synthesize an answer using LLM reasoning over recalled Hindsight memories.
    """
    if not memories:
        return (
            f"Foresight evaluated your query ('{question}') against PayNest's incident memory bank. "
            f"No direct historical incident matched this specific prompt. Always follow standard deploy safety: "
            f"deploy via canary, monitor gateway metrics, and enforce idempotency key headers."
        )

    # In live mode with Groq configured, LLM performs completion reasoning over recalled memories
    system_prompt = (
        "You are Foresight, an AI deploy-safety agent for PayNest fintech platform. "
        "Answer the user's question directly and informatively using the provided recalled Hindsight incident memories. "
        "Provide a clear, structured, markdown-formatted response detailing what happened, root causes, services affected, and preventative safety steps."
    )

    mem_context = "\n".join(
        [
            f"• Incident Document [{m.get('id', 'mem')}]: {m.get('text', m.get('content', ''))}"
            for m in memories
        ]
    )

    prompt = f"USER QUESTION: {question}\n\nRECALLED HINDSIGHT MEMORIES:\n{mem_context}\n\nPlease synthesize a clear, comprehensive answer for the user based on these recalled memories:"

    # Use LLM client for synthesis
    try:
        if llm_client.is_live():
            raw_response = llm_client._call_groq(
                model=llm_client.primary_model,
                prompt=prompt,
                system_prompt=system_prompt,
            )
            if raw_response and len(raw_response.strip()) > 10:
                text = raw_response.strip()
                if text.startswith("{") and text.endswith("}"):
                    try:
                        parsed = json.loads(text)
                        for k in ["answer", "summary", "response", "message"]:
                            if k in parsed and isinstance(parsed[k], str):
                                return parsed[k].strip()
                    except Exception:
                        pass
                return text
    except Exception as e:
        pass

    # Deterministic synthesis over recalled memories if offline or fallback
    insights = []
    for m in memories[:3]:
        m_id = m.get("id", "INC")
        m_text = m.get("text", m.get("content", ""))
        insights.append(f"• **[{m_id}]**: {m_text}")

    synthesis = (
        f"Based on {len(memories)} recalled memories in Hindsight memory for query '{question}':\n\n"
        + "\n\n".join(insights)
        + "\n\n**Foresight Recommendation:** Verify that all proposed configuration changes align with past postmortem fixes and run through a canary deployment."
    )
    return synthesis


async def generate_ask_stream(question: str):
    # 1. Recall relevant memories from Hindsight
    memories = memory_service.recall(query=question, limit=5)

    citations = [
        {
            "id": m.get("id", "mem-1"),
            "text": m.get("text", m.get("content", "")),
            "score": m.get("score", 0.9),
            "tags": m.get("tags", []),
        }
        for m in memories
    ]

    # First event: yield citations
    yield json.dumps({"type": "citations", "citations": citations}) + "\n"

    # 2. Synthesize answer using Hindsight recall + LLM reasoning
    answer = synthesize_answer_from_memories(question, memories)

    # 3. Stream text chunks
    words = answer.split(" ")
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i : i + 3])
        if i + 3 < len(words):
            chunk += " "
        yield json.dumps({"type": "delta", "text": chunk}) + "\n"
        await asyncio.sleep(0.02)

    yield json.dumps({"type": "done"}) + "\n"


@router.post("/ask")
async def ask_foresight(request: AskRequest):
    try:
        return StreamingResponse(
            generate_ask_stream(request.question),
            media_type="application/x-ndjson",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "ASK_ERROR", "message": str(e)}},
        )
