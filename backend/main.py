"""FastAPI backend for conversation dataset viewer."""
import json
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, Conversation, init_db

# Initialize FastAPI app
app = FastAPI(title="Conversation Dataset API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Pydantic models for API responses
class ConversationResponse(BaseModel):
    id: str
    task_id: int
    personality: str
    problem_text: str
    test_cases: List[str]
    conversation: List[dict]
    execution_result: Optional[dict]
    solved: bool
    tests_passed: int
    total_tests: int
    turns: int
    timestamp: str
    date_folder: str
    discarded: bool
    
    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: str
    task_id: int
    personality: str
    problem_text: str
    solved: bool
    tests_passed: int
    total_tests: int
    turns: int
    discarded: bool


# API Endpoints

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Conversation Dataset API"}


@app.get("/api/dates", response_model=List[str])
def get_dates(db: Session = Depends(get_db)):
    """Get list of available date folders."""
    dates = db.query(Conversation.date_folder).distinct().all()
    date_list = [d[0] for d in dates]
    # Sort in reverse chronological order
    date_list.sort(reverse=True)
    return date_list


@app.get("/api/personalities/{date}", response_model=List[str])
def get_personalities(date: str, db: Session = Depends(get_db)):
    """Get list of personalities for a specific date."""
    personalities = db.query(Conversation.personality).filter(
        Conversation.date_folder == date
    ).distinct().all()
    return sorted([p[0] for p in personalities])


@app.get("/api/conversations/{date}/{personality}", response_model=List[ConversationSummary])
def get_conversations(
    date: str, 
    personality: str, 
    include_discarded: bool = False,
    db: Session = Depends(get_db)
):
    """Get all conversations for a specific date and personality."""
    query = db.query(Conversation).filter(
        Conversation.date_folder == date,
        Conversation.personality == personality
    )
    
    if not include_discarded:
        query = query.filter(Conversation.discarded == False)
    
    conversations = query.all()
    
    # Convert to summary format
    summaries = []
    for conv in conversations:
        summaries.append(ConversationSummary(
            id=conv.id,
            task_id=conv.task_id,
            personality=conv.personality,
            problem_text=conv.problem_text,
            solved=conv.solved,
            tests_passed=conv.tests_passed,
            total_tests=conv.total_tests,
            turns=conv.turns,
            discarded=conv.discarded
        ))
    
    return summaries


@app.get("/api/conversation/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get full details of a specific conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationResponse(
        id=conv.id,
        task_id=conv.task_id,
        personality=conv.personality,
        problem_text=conv.problem_text,
        test_cases=json.loads(conv.test_cases),
        conversation=json.loads(conv.conversation),
        execution_result=json.loads(conv.execution_result) if conv.execution_result else None,
        solved=conv.solved,
        tests_passed=conv.tests_passed,
        total_tests=conv.total_tests,
        turns=conv.turns,
        timestamp=conv.timestamp,
        date_folder=conv.date_folder,
        discarded=conv.discarded
    )


@app.patch("/api/conversations/{conversation_id}/discard")
def toggle_discard(conversation_id: str, db: Session = Depends(get_db)):
    """Toggle the discard status of a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv.discarded = not conv.discarded
    db.commit()
    
    return {"id": conversation_id, "discarded": conv.discarded}


@app.get("/api/stats/{date}/{personality}")
def get_stats(date: str, personality: str, db: Session = Depends(get_db)):
    """Get statistics for conversations."""
    conversations = db.query(Conversation).filter(
        Conversation.date_folder == date,
        Conversation.personality == personality,
        Conversation.discarded == False
    ).all()
    
    if not conversations:
        return {
            "total": 0,
            "solved": 0,
            "avg_turns": 0,
            "total_tests_passed": 0,
            "total_tests_possible": 0
        }
    
    solved_count = sum(1 for c in conversations if c.solved)
    avg_turns = sum(c.turns for c in conversations) / len(conversations)
    total_tests_passed = sum(c.tests_passed for c in conversations)
    total_tests_possible = sum(c.total_tests for c in conversations)
    
    return {
        "total": len(conversations),
        "solved": solved_count,
        "avg_turns": round(avg_turns, 1),
        "total_tests_passed": total_tests_passed,
        "total_tests_possible": total_tests_possible
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
