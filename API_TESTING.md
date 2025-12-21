# API Testing Examples

## Test the Backend Directly

Once your backend is running on http://localhost:8000, you can test the API directly.

## Interactive API Documentation

Visit: http://localhost:8000/docs

This provides a Swagger UI where you can test all endpoints interactively.

## Manual Testing with curl

### 1. Create a Meeting

```bash
curl -X POST "http://localhost:8000/api/meetings" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Q1 Planning Meeting",
    "meeting_date": "2024-01-15",
    "meeting_purpose": "Discuss Q1 objectives and key results",
    "agenda_items": [
      {"item": "Review Q4 performance", "notes": "Exceeded targets by 15%"},
      {"item": "Set Q1 OKRs", "notes": "Focus on customer acquisition"}
    ],
    "attendees": [
      {"name": "John Smith", "attended": true},
      {"name": "Sarah Johnson", "attended": true},
      {"name": "Mike Chen", "attended": false}
    ],
    "action_items": [
      {
        "description": "Prepare Q1 budget proposal",
        "owner": "John Smith",
        "due_date": "2024-01-20",
        "status": "Pending"
      },
      {
        "description": "Draft marketing campaign plan",
        "owner": "Sarah Johnson",
        "due_date": "2024-01-25",
        "status": "In Progress"
      }
    ]
  }'
```

### 2. Get All Meetings

```bash
curl -X GET "http://localhost:8000/api/meetings"
```

### 3. Get Specific Meeting

```bash
# Replace {id} with the actual meeting ID
curl -X GET "http://localhost:8000/api/meetings/1"
```

### 4. Update a Meeting

```bash
curl -X PUT "http://localhost:8000/api/meetings/1" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Q1 Planning Meeting - UPDATED",
    "meeting_date": "2024-01-15",
    "meeting_purpose": "Updated: Discuss Q1 objectives and key results",
    "agenda_items": [
      {"item": "Review Q4 performance", "notes": "Exceeded targets by 15%"}
    ],
    "attendees": [
      {"name": "John Smith", "attended": true}
    ],
    "action_items": [
      {
        "description": "Prepare Q1 budget proposal",
        "owner": "John Smith",
        "due_date": "2024-01-20",
        "status": "Completed"
      }
    ]
  }'
```

### 5. Delete a Meeting

```bash
curl -X DELETE "http://localhost:8000/api/meetings/1"
```

### 6. Export Meeting to DOCX

```bash
# This will download the DOCX file
curl -X GET "http://localhost:8000/api/meetings/1/export" \
  --output meeting_minutes.docx
```

## AI Features Testing (Costs Tokens)

### 7. Upload a Screenshot (No Token Cost)

```bash
curl -X POST "http://localhost:8000/api/screenshots/upload" \
  -F "file=@/path/to/your/screenshot.png"
```

Response example:
```json
{
  "success": true,
  "file_path": "/full/path/to/uploaded/file.png",
  "filename": "screenshot.png"
}
```

### 8. Analyze Screenshot (Costs Tokens)

```bash
curl -X POST "http://localhost:8000/api/screenshots/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/full/path/to/uploaded/file.png",
    "context": "Screenshot from project planning meeting"
  }'
```

### 9. Identify Speakers (Costs Tokens)

```bash
curl -X POST "http://localhost:8000/api/screenshots/identify-speakers" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/full/path/to/uploaded/file.png"
  }'
```

### 10. AI Generate Meeting Minutes (Costs Tokens)

```bash
curl -X POST "http://localhost:8000/api/meetings/ai-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_notes": "Meeting with development team. Attendees: John Smith (PM), Sarah Johnson (Dev Lead). Discussed: 1) Frontend redesign - Sarah will lead, due Feb 15. 2) API improvements - Mike to investigate. Action items: Sarah to complete mockups by Jan 30.",
    "additional_context": "Q1 Planning Session"
  }'
```

## Python Testing Script

Create `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_create_meeting():
    """Test creating a meeting"""
    meeting = {
        "project_name": "Test Meeting",
        "meeting_date": "2024-01-15",
        "meeting_purpose": "Testing the API",
        "agenda_items": [
            {"item": "Test agenda", "notes": "Test notes"}
        ],
        "attendees": [
            {"name": "Test User", "attended": True}
        ],
        "action_items": [
            {
                "description": "Test action",
                "owner": "Test User",
                "due_date": "2024-01-20",
                "status": "Pending"
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/meetings", json=meeting)
    print(f"Create Meeting Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_meetings():
    """Test getting all meetings"""
    response = requests.get(f"{BASE_URL}/meetings")
    print(f"Get Meetings Status: {response.status_code}")
    print(f"Number of meetings: {len(response.json())}")
    return response.json()

def test_export_meeting(meeting_id):
    """Test exporting a meeting to DOCX"""
    response = requests.get(f"{BASE_URL}/meetings/{meeting_id}/export")
    print(f"Export Status: {response.status_code}")

    if response.status_code == 200:
        with open(f"test_meeting_{meeting_id}.docx", "wb") as f:
            f.write(response.content)
        print(f"✅ Exported to test_meeting_{meeting_id}.docx")

if __name__ == "__main__":
    print("🧪 Testing Meeting Minutes API\n")

    # Create a test meeting
    print("1️⃣ Creating test meeting...")
    created = test_create_meeting()
    print()

    # Get all meetings
    print("2️⃣ Getting all meetings...")
    meetings = test_get_meetings()
    print()

    # Export the meeting
    if created.get("id"):
        print(f"3️⃣ Exporting meeting {created['id']}...")
        test_export_meeting(created["id"])
        print()

    print("✅ API tests complete!")
```

Run with:
```bash
cd /Users/andrewmorton/Documents/GitHub/meeting-minutes-app
python test_api.py
```

## JavaScript Testing Script

Create `test_api.js`:

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api';

async function testCreateMeeting() {
  const meeting = {
    project_name: 'Test Meeting',
    meeting_date: '2024-01-15',
    meeting_purpose: 'Testing the API',
    agenda_items: [
      { item: 'Test agenda', notes: 'Test notes' }
    ],
    attendees: [
      { name: 'Test User', attended: true }
    ],
    action_items: [
      {
        description: 'Test action',
        owner: 'Test User',
        due_date: '2024-01-20',
        status: 'Pending'
      }
    ]
  };

  const response = await axios.post(`${BASE_URL}/meetings`, meeting);
  console.log('Create Meeting Status:', response.status);
  console.log('Response:', JSON.stringify(response.data, null, 2));
  return response.data;
}

async function testGetMeetings() {
  const response = await axios.get(`${BASE_URL}/meetings`);
  console.log('Get Meetings Status:', response.status);
  console.log('Number of meetings:', response.data.length);
  return response.data;
}

async function main() {
  console.log('🧪 Testing Meeting Minutes API\n');

  try {
    console.log('1️⃣ Creating test meeting...');
    const created = await testCreateMeeting();
    console.log();

    console.log('2️⃣ Getting all meetings...');
    await testGetMeetings();
    console.log();

    console.log('✅ API tests complete!');
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

main();
```

## Health Check

Simple health check endpoint:

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Meeting Minutes API",
  "version": "1.0.0"
}
```

## Common Status Codes

- `200` - Success
- `201` - Created (for POST requests)
- `404` - Not found
- `422` - Validation error (bad request data)
- `500` - Server error

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Health check returns 200
- [ ] Can create a meeting
- [ ] Can retrieve meetings
- [ ] Can update a meeting
- [ ] Can delete a meeting
- [ ] Can export to DOCX
- [ ] DOCX file matches template structure
- [ ] Screenshot upload works
- [ ] AI features work (if enabled)

## Debugging Tips

1. **Check backend logs** - Look at the terminal running the backend
2. **Verify template path** - Ensure the template file exists
3. **Check database** - `ls -la backend/meetings.db`
4. **API documentation** - Visit http://localhost:8000/docs
5. **Network tab** - Use browser dev tools to inspect requests

---

**All API endpoints are documented at http://localhost:8000/docs when the backend is running!**
