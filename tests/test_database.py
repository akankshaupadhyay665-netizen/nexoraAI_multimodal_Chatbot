"""
Nexora AI - Database Persistence Tests
"""
import uuid
from backend.database import SessionLocal, Base, engine
from backend.models import Conversation, Message, UploadedFile, GeneratedMedia, VideoJob

def test_database_tables_exist():
    """Verify all database tables compile and initialize"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create test conversation
        test_id = str(uuid.uuid4())
        conv = Conversation(id=test_id, title="DB Test Conversation", model_used="gemini-2.5-flash")
        db.add(conv)
        db.commit()

        # Add message
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=test_id,
            role="user",
            content="Testing database persistence"
        )
        db.add(msg)
        db.commit()

        # Query and verify
        retrieved = db.query(Conversation).filter(Conversation.id == test_id).first()
        assert retrieved is not None
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].content == "Testing database persistence"

        # Cleanup
        db.delete(retrieved)
        db.commit()
    finally:
        db.close()

