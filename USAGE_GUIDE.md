# Meeting Minutes App - Usage Guide

## Overview

This application helps you create, manage, and export professional meeting minutes using your custom template. It includes optional AI-powered features to automatically extract information from screenshots and generate structured meeting minutes.

## Features

### Core Features (No AI Required)
- ✅ Create and edit meeting minutes manually
- ✅ Store meetings in a local database
- ✅ Export to DOCX using your template
- ✅ Track agenda items, attendees, and action items
- ✅ Upload and store meeting screenshots

### AI Features (Optional - Costs Tokens)
- 🤖 Auto-generate meeting minutes from notes/transcripts
- 🤖 Extract information from screenshots
- 🤖 Identify speakers from meeting screenshots
- 🤖 Analyze meeting content and structure data

**Important:** AI features are completely optional and clearly marked to help you manage token costs.

## Quick Start

### 1. Install Dependencies

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Start the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```
Backend runs on http://localhost:8000

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on http://localhost:5173

### 3. Open the App

Navigate to http://localhost:5173 in your browser

## Creating Meeting Minutes

### Manual Method (Recommended for Most Use Cases)

1. Click "New Meeting" in the navigation
2. Fill in the basic information:
   - Project Name
   - Meeting Date
   - Meeting Purpose
3. Add Agenda Items:
   - Click "+ Add Item"
   - Enter item name and notes
4. Add Attendees:
   - Click "+ Add Attendee"
   - Enter name and check if they attended
5. Add Action Items:
   - Click "+ Add Action Item"
   - Enter description, owner, due date, and status
6. Click "Create Meeting"

### AI-Assisted Method (Uses Tokens - Use Sparingly)

1. Click "New Meeting"
2. Click "Use AI Assistant (Optional)"
3. Paste your meeting notes or transcript
4. Optionally upload screenshots from the meeting
5. Click "Generate Meeting Minutes with AI"
6. Review and edit the AI-generated content
7. Click "Create Meeting"

**When to use AI:**
- Long meetings with extensive notes
- Screenshots with important data/charts
- When you need speaker identification
- Time-sensitive situations

**When NOT to use AI:**
- Short, simple meetings
- When you already have structured notes
- To save on token costs

## Exporting to DOCX

1. From the Meeting List, find your meeting
2. Click the Download icon
3. The DOCX file will be downloaded automatically
4. Open in Microsoft Word or compatible software

The export uses your template at:
`/Users/andrewmorton/Downloads/Meeting Agenda Template v1- short form.docx`

## Screenshot Features

### Upload Screenshots (No Token Cost)
- Drag and drop images into the AI Assistant area
- Or click to browse and select files
- Supports PNG, JPG, JPEG formats
- Screenshots are stored locally

### AI Screenshot Analysis (Costs Tokens)
Once uploaded, screenshots can be analyzed to extract:
- Key topics and discussion points
- Visible text and data
- Speaker names (if visible)
- Charts and visual information

**Tip:** Upload screenshots first, then decide if you need AI analysis.

## Managing Token Costs

### Zero Token Usage:
- Manual entry of all fields
- Upload screenshots without analysis
- Edit existing meetings
- Export to DOCX

### Low Token Usage (~500-1000 tokens):
- Analyze 1-2 screenshots
- Generate minutes from brief notes

### Medium Token Usage (~2000-3000 tokens):
- Generate minutes from extensive notes
- Analyze 5+ screenshots

### Tips to Minimize Costs:
1. Use AI only when it saves significant time
2. Pre-process your notes before AI generation
3. Use manual entry for simple meetings
4. Review AI output and make manual corrections

## Database

Meetings are stored in: `backend/meetings.db`

### Backup Your Data:
```bash
cp backend/meetings.db backend/meetings_backup.db
```

### Reset Database:
```bash
rm backend/meetings.db
# Restart backend to create fresh database
```

## Troubleshooting

### Backend won't start:
- Check if port 8000 is available
- Ensure virtual environment is activated
- Verify all dependencies are installed

### Frontend won't start:
- Check if port 5173 is available
- Run `npm install` again
- Clear npm cache: `npm cache clean --force`

### Export not working:
- Verify template file exists at the specified path
- Check backend logs for errors
- Ensure python-docx is installed

### AI features not working:
- Verify ANTHROPIC_API_KEY is set in environment
- Check backend logs for API errors
- Ensure you have API credits available

## API Endpoints

### Meetings
- `GET /api/meetings` - List all meetings
- `GET /api/meetings/{id}` - Get specific meeting
- `POST /api/meetings` - Create new meeting
- `PUT /api/meetings/{id}` - Update meeting
- `DELETE /api/meetings/{id}` - Delete meeting
- `GET /api/meetings/{id}/export` - Export to DOCX

### Screenshots (Optional AI)
- `POST /api/screenshots/upload` - Upload screenshot (no cost)
- `POST /api/screenshots/analyze` - Analyze with AI (costs tokens)
- `POST /api/screenshots/identify-speakers` - Identify speakers (costs tokens)
- `POST /api/screenshots/crop` - Crop/enhance (no cost)

### AI Generation (Optional)
- `POST /api/meetings/ai-generate` - Generate meeting minutes (costs tokens)

## Best Practices

1. **Start Simple:** Use manual entry first to understand the workflow
2. **Use AI Strategically:** Only when it provides clear time savings
3. **Review AI Output:** Always review and edit AI-generated content
4. **Regular Backups:** Backup your database regularly
5. **Clean Screenshots:** For best AI results, use clear, high-resolution screenshots
6. **Structured Notes:** Well-organized notes produce better AI results

## Support

For issues or questions:
- Check the README.md
- Review backend logs
- Check browser console for frontend errors
- Ensure all dependencies are up to date
