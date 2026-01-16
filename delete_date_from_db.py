"""Delete conversations from a specific date folder in the database."""
import sys
from backend.database import SessionLocal, Conversation

def delete_date(date_folder):
    """Delete all conversations from a specific date folder."""
    db = SessionLocal()
    try:
        deleted = db.query(Conversation).filter(
            Conversation.date_folder == date_folder
        ).delete()
        db.commit()
        print(f"✅ Deleted {deleted} conversations from {date_folder}")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_date_from_db.py <date_folder>")
        print("Example: python delete_date_from_db.py 14_01_2026")
        sys.exit(1)
    
    date_folder = sys.argv[1]
    delete_date(date_folder)
