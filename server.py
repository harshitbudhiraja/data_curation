from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from llm_calling import call_llm_openrouter
import uvicorn

app = FastAPI()


class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    system_prompt: Optional[str] = "You are a helpful assistant."
    model: Optional[str] = "qwen/qwen3-8b"


# class ChatResponse(BaseModel):
#     response: str


@app.post("/chat", response_model=str)
async def chat(request: ChatRequest):
    """
    Chat endpoint that calls the LLM via OpenRouter.
    """
    print(request, type(request))
    try:
        response = call_llm_openrouter(
            user_prompt=request.prompt,
            system_prompt=request.system_prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}") from e


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

