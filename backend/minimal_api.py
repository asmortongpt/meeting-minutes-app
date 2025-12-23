"""
Minimal Meeting Minutes API - Fast startup with database support
"""
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import json
from pathlib import Path

app = FastAPI(title="Meeting Minutes API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = Path(__file__).parent / "meetings.db"

# Pydantic models
class AgendaItem(BaseModel):
    item: str
    notes: str = ""

class Attendee(BaseModel):
    name: str
    attended: bool = True

class ActionItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    status: str = "pending"
    priority: Optional[str] = "medium"

class MeetingMinutes(BaseModel):
    id: Optional[int] = None
    title: str
    meeting_date: str
    duration: Optional[int] = None
    attendees: List[Attendee] = []
    topics: List[str] = []
    action_items: List[ActionItem] = []
    decisions: List[str] = []
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    project_category: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            duration INTEGER,
            attendees TEXT,
            topics TEXT,
            action_items TEXT,
            decisions TEXT,
            summary TEXT,
            sentiment TEXT,
            project_category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Initialize database on startup (runs once)
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization issue: {e}")

@app.get("/")
async def root():
    return {"message": "Meeting Minutes API", "status": "running", "version": "1.0"}

@app.get("/api/meetings")
async def get_meetings():
    """Get all meetings"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM meetings ORDER BY meeting_date DESC")
        rows = cursor.fetchall()

        meetings = []
        for row in rows:
            meeting = {
                "id": row["id"],
                "title": row["title"],
                "meeting_date": row["meeting_date"],
                "duration": row["duration"],
                "attendees": json.loads(row["attendees"]) if row["attendees"] else [],
                "topics": json.loads(row["topics"]) if row["topics"] else [],
                "action_items": json.loads(row["action_items"]) if row["action_items"] else [],
                "decisions": json.loads(row["decisions"]) if row["decisions"] else [],
                "summary": row["summary"],
                "sentiment": row["sentiment"],
                "project_category": row["project_category"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            meetings.append(meeting)

        conn.close()
        return meetings
    except Exception as e:
        print(f"Error getting meetings: {e}")
        return []

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Get a specific meeting"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting = {
        "id": row["id"],
        "title": row["title"],
        "meeting_date": row["meeting_date"],
        "duration": row["duration"],
        "attendees": json.loads(row["attendees"]) if row["attendees"] else [],
        "topics": json.loads(row["topics"]) if row["topics"] else [],
        "action_items": json.loads(row["action_items"]) if row["action_items"] else [],
        "decisions": json.loads(row["decisions"]) if row["decisions"] else [],
        "summary": row["summary"],
        "sentiment": row["sentiment"],
        "project_category": row["project_category"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

    conn.close()
    return meeting

@app.post("/api/meetings")
async def create_meeting(meeting: MeetingMinutes):
    """Create a new meeting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meetings (
            title, meeting_date, duration, attendees, topics,
            action_items, decisions, summary, sentiment, project_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting.title,
        meeting.meeting_date,
        meeting.duration,
        json.dumps([att.model_dump() for att in meeting.attendees]),
        json.dumps(meeting.topics),
        json.dumps([action.model_dump() for action in meeting.action_items]),
        json.dumps(meeting.decisions),
        meeting.summary,
        meeting.sentiment,
        meeting.project_category
    ))

    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": meeting_id, "message": "Meeting created successfully"}

@app.put("/api/meetings/{meeting_id}")
async def update_meeting(meeting_id: int, meeting: MeetingMinutes):
    """Update a meeting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meetings SET
            title = ?,
            meeting_date = ?,
            duration = ?,
            attendees = ?,
            topics = ?,
            action_items = ?,
            decisions = ?,
            summary = ?,
            sentiment = ?,
            project_category = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        meeting.title,
        meeting.meeting_date,
        meeting.duration,
        json.dumps([att.model_dump() for att in meeting.attendees]),
        json.dumps(meeting.topics),
        json.dumps([action.model_dump() for action in meeting.action_items]),
        json.dumps(meeting.decisions),
        meeting.summary,
        meeting.sentiment,
        meeting.project_category,
        meeting_id
    ))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Meeting not found")

    conn.commit()
    conn.close()

    return {"message": "Meeting updated successfully"}

@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int):
    """Delete a meeting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Meeting not found")

    conn.commit()
    conn.close()

    return {"message": "Meeting deleted successfully"}

@app.post("/api/upload")
async def upload_meeting_file(file: UploadFile = File(...)):
    """Upload and process a meeting file"""
    # For now, return mock analysis data
    # In production, this would call the AI processor
    return {
        "status": "success",
        "analysis": {
            "title": f"Meeting from {file.filename}",
            "meeting_date": datetime.now().isoformat(),
            "duration": 45,
            "attendees": [
                {"name": "Andrew Morton", "attended": True},
                {"name": "Sarah Johnson", "attended": True},
                {"name": "Mike Chen", "attended": True}
            ],
            "topics": ["API Development", "Infrastructure", "Budget Review"],
            "action_items": [
                {
                    "task": "Complete infrastructure deployment",
                    "assignee": "Mike Chen",
                    "due_date": "2024-12-27",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "task": "Review and approve budget proposal",
                    "assignee": "Andrew Morton",
                    "due_date": "2024-12-24",
                    "status": "pending",
                    "priority": "high"
                }
            ],
            "decisions": [
                "Approved infrastructure deployment timeline",
                "Deferred marketing budget decision to next meeting"
            ],
            "summary": "Team discussed API development progress, infrastructure deployment plans, and reviewed the Q4 budget proposal. Key decisions made regarding deployment timeline.",
            "sentiment": "positive",
            "project_category": "Infrastructure"
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy", "database": str(DB_PATH.exists())}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
