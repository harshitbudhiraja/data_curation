"""SQLite database setup for conversation storage."""
import json
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup - use absolute path
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "conversations.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Conversation(Base):
    """Conversation model for storing student-tutor interactions."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(Integer, index=True)
    personality = Column(String, index=True)
    problem_text = Column(Text)
    test_cases = Column(Text)  # JSON string
    conversation = Column(Text)  # JSON string
    execution_result = Column(Text)  # JSON string
    solved = Column(Boolean, default=False)
    tests_passed = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    turns = Column(Integer, default=0)
    timestamp = Column(String)
    date_folder = Column(String, index=True)
    discarded = Column(Boolean, default=False, index=True)
    quality_bucket = Column(String, index=True)  # "gold", "silver", "bronze", or None


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_json_to_db():
    """Migrate existing JSON conversation files to SQLite database."""
    from sqlalchemy.orm import Session
    
    init_db()
    db = SessionLocal()
    
    # Use absolute path for data directory (parent of backend)
    data_dir = BASE_DIR.parent / "data"
    if not data_dir.exists():
        print(f"No data directory found at {data_dir}")
        return
    
    total_imported = 0
    
    # Iterate through date folders
    for date_folder in data_dir.iterdir():
        if not date_folder.is_dir() or date_folder.name.startswith('.'):
            continue
        
        print(f"Processing {date_folder.name}...")
        
        # Find all conversation JSON files
        for json_file in date_folder.glob("*_conversations.json"):
            try:
                with open(json_file, 'r') as f:
                    conversations = json.load(f)
                
                for conv in conversations:
                    # Check if already exists
                    existing = db.query(Conversation).filter(
                        Conversation.id == conv['id']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Handle both Strategy 1 (personality) and Strategy 2 (knowledge_level)
                    personality_value = conv.get('personality') or conv.get('knowledge_level')
                    
                    if not personality_value:
                        print(f"  ⚠️  Skipping conversation {conv.get('id', 'unknown')}: missing personality/knowledge_level")
                        continue
                    
                    # Create new conversation record
                    db_conv = Conversation(
                        id=conv['id'],
                        task_id=conv['task_id'],
                        personality=personality_value,
                        problem_text=conv['problem_text'],
                        test_cases=json.dumps(conv['test_cases']),
                        conversation=json.dumps(conv['conversation']),
                        execution_result=json.dumps(conv.get('execution_result')),
                        solved=conv.get('solved', False),
                        tests_passed=conv.get('tests_passed', 0),
                        total_tests=conv.get('total_tests', 0),
                        turns=conv.get('turns', 0),
                        timestamp=conv.get('timestamp', ''),
                        date_folder=date_folder.name,
                        discarded=False,
                        quality_bucket=conv.get('quality_bucket')  # Import quality if exists
                    )
                    db.add(db_conv)
                    total_imported += 1
                
                db.commit()
                print(f"  ✅ Imported {json_file.name}")
                
            except Exception as e:
                print(f"  ❌ Error importing {json_file.name}: {e}")
                db.rollback()
    
    db.close()
    print(f"\n🎉 Migration complete! Imported {total_imported} conversations")


if __name__ == "__main__":
    migrate_json_to_db()
