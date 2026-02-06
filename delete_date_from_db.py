"""Delete conversations from a specific date folder or all data from the database."""
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

def delete_all():
    """Delete all conversations from the database."""
    db = SessionLocal()
    try:
        count = db.query(Conversation).count()
        print(f"Found {count} conversations in database")
        
        if count == 0:
            print("Database is already empty!")
            return
        
        confirm = input(f"\n⚠️  Are you sure you want to delete ALL {count} conversations? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return
        
        deleted = db.query(Conversation).delete()
        db.commit()
        print(f"✅ Successfully deleted {deleted} conversations from database")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  Delete specific date: python delete_date_from_db.py <date_folder>")
        print("  Delete all data:      python delete_date_from_db.py --all")
        print("\nExample: python delete_date_from_db.py 14_01_2026")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        delete_all()
    else:
        date_folder = sys.argv[1]
        delete_date(date_folder)
