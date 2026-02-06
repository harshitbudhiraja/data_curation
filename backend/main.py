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
    allow_origins=["*"],
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
    quality_bucket: Optional[str] = None
    quality_scores: Optional[dict] = None
    
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
    quality_bucket: Optional[str] = None


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
    quality: Optional[str] = None,  # Filter by quality: "gold", "silver", "bronze", or None for all
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
    
    # Filter by quality if specified
    if quality and quality != "all":
        query = query.filter(Conversation.quality_bucket == quality)
    
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
            discarded=conv.discarded,
            quality_bucket=conv.quality_bucket
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
        discarded=conv.discarded,
        quality_bucket=conv.quality_bucket,
        quality_scores=json.loads(conv.conversation)[0].get('quality_scores') if conv.conversation else None
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
            "total_tests_possible": 0,
            "quality": {
                "gold": 0,
                "silver": 0,
                "bronze": 0,
                "unverified": 0
            }
        }
    
    solved_count = sum(1 for c in conversations if c.solved)
    avg_turns = sum(c.turns for c in conversations) / len(conversations)
    total_tests_passed = sum(c.tests_passed for c in conversations)
    total_tests_possible = sum(c.total_tests for c in conversations)
    
    # Count quality buckets
    gold_count = sum(1 for c in conversations if c.quality_bucket == 'gold')
    silver_count = sum(1 for c in conversations if c.quality_bucket == 'silver')
    bronze_count = sum(1 for c in conversations if c.quality_bucket == 'bronze')
    unverified_count = sum(1 for c in conversations if not c.quality_bucket)
    
    return {
        "total": len(conversations),
        "solved": solved_count,
        "avg_turns": round(avg_turns, 1),
        "total_tests_passed": total_tests_passed,
        "total_tests_possible": total_tests_possible,
        "quality": {
            "gold": gold_count,
            "silver": silver_count,
            "bronze": bronze_count,
            "unverified": unverified_count
        }
    }


@app.get("/api/coding-questions")
def get_coding_questions():
    """Get all coding questions from the benchmark dataset."""
    import os
    
    # Path to the coding questions file
    questions_path = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "coding_questions_500.json")
    
    try:
        with open(questions_path, 'r') as f:
            questions = json.load(f)
        return questions
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Coding questions file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing coding questions file")


@app.get("/api/coding-questions/{task_id}")
def get_coding_question(task_id: int):
    """Get a specific coding question by task_id."""
    import os
    
    questions_path = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "coding_questions_500.json")
    
    try:
        with open(questions_path, 'r') as f:
            questions = json.load(f)
        
        # Find the question with the matching task_id
        question = next((q for q in questions if q['task_id'] == task_id), None)
        
        if not question:
            raise HTTPException(status_code=404, detail=f"Question with task_id {task_id} not found")
        
        return question
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Coding questions file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing coding questions file")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
