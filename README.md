# Meeting Minutes App

A professional web application for creating, managing, and exporting meeting minutes using your custom DOCX template.

## Features

### Core Features ✅
- ✅ **Manual Entry**: Create meeting minutes with an intuitive form interface
- ✅ **Database Storage**: SQLite database for persistent storage
- ✅ **Template Export**: Export to DOCX using your exact template format
- ✅ **Full CRUD**: Create, read, update, delete meeting records
- ✅ **Screenshot Storage**: Upload and store meeting screenshots

### AI-Powered Features 🤖 (Optional - Use Sparingly)
- 🤖 **Auto-Generate Minutes**: AI analyzes notes and creates structured minutes
- 🤖 **Screenshot Analysis**: Extract text, data, and insights from images
- 🤖 **Speaker Identification**: Identify participants from screenshots
- 🤖 **Smart Content Extraction**: Pull out agenda items, action items, attendees

**AI features are clearly marked and entirely optional to help manage token costs.**

## Tech Stack

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite
- **AI**: Anthropic Claude (Sonnet 3.5)
- **Export**: python-docx
- **Image Processing**: Pillow

## Quick Start

### Option 1: Easy Launch (Recommended)
```bash
cd /Users/andrewmorton/Documents/GitHub/meeting-minutes-app
./start-app.sh
```
This opens the backend and frontend in separate terminal windows.

### Option 2: Manual Launch

**Terminal 1 - Backend:**
```bash
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start-frontend.sh
```

### Option 3: Step-by-Step

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## How to Use

### Creating a Meeting (Manual)
1. Click "New Meeting"
2. Fill in project name, date, and purpose
3. Add agenda items, attendees, and action items
4. Click "Create Meeting"
5. Export to DOCX from the meeting list

### Creating a Meeting (AI-Assisted)
1. Click "New Meeting"
2. Click "Use AI Assistant (Optional)"
3. Paste meeting notes or transcript
4. Upload screenshots (optional)
5. Click "Generate Meeting Minutes with AI"
6. Review and edit the generated content
7. Click "Create Meeting"

### Exporting to DOCX
1. Find your meeting in the list
2. Click the Download icon
3. The DOCX file downloads using your template

## Template Configuration

The app uses your template located at:
```
/Users/andrewmorton/Downloads/Meeting Agenda Template v1- short form.docx
```

To use a different template, update the `TEMPLATE_PATH` in `backend/main.py` line 40.

## Managing AI Token Costs

### Zero Tokens:
- Manual data entry
- Screenshot upload (without analysis)
- Editing existing meetings
- Exporting to DOCX

### Token Usage:
- Screenshot analysis: ~200-500 tokens each
- Meeting generation: ~1000-3000 tokens depending on content length

### Tips:
1. Use AI only for complex meetings
2. Upload screenshots but only analyze when needed
3. Keep meeting notes concise
4. Review and edit AI output

## Project Structure

```
meeting-minutes-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ai_analyzer.py       # AI analysis module
│   ├── requirements.txt     # Python dependencies
│   ├── meetings.db          # SQLite database
│   ├── uploads/             # Screenshot storage
│   └── exports/             # Generated DOCX files
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main app component
│   │   ├── pages/
│   │   │   ├── MeetingForm.tsx
│   │   │   └── MeetingList.tsx
│   │   └── services/
│   │       └── api.ts       # API client
│   └── package.json
├── start-app.sh             # Launch everything
├── start-backend.sh         # Launch backend only
├── start-frontend.sh        # Launch frontend only
├── USAGE_GUIDE.md          # Detailed usage instructions
└── README.md               # This file
```

## API Endpoints

See full API documentation at http://localhost:8000/docs when the backend is running.

### Key Endpoints:
- `GET /api/meetings` - List all meetings
- `POST /api/meetings` - Create new meeting
- `GET /api/meetings/{id}/export` - Export to DOCX
- `POST /api/screenshots/upload` - Upload screenshot (free)
- `POST /api/meetings/ai-generate` - AI generation (costs tokens)

## Troubleshooting

### Backend Issues
```bash
# Check if port 8000 is in use
lsof -i :8000

# Reinstall dependencies
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Template Not Found
Update the template path in `backend/main.py`:
```python
TEMPLATE_PATH = Path("/path/to/your/template.docx")
```

## Database Backup

```bash
# Backup
cp backend/meetings.db backend/meetings_backup_$(date +%Y%m%d).db

# Restore
cp backend/meetings_backup_20231219.db backend/meetings.db
```

## Security Notes

- Database is local SQLite (no network exposure)
- API keys stored in environment variables
- CORS configured for localhost development
- File uploads restricted to images

## Future Enhancements

- [ ] Audio transcription support
- [ ] Real-time collaboration
- [ ] Multiple template support
- [ ] PDF export option
- [ ] Calendar integration
- [ ] Email distribution

## Documentation

- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage instructions
- API Docs: http://localhost:8000/docs (when running)

## Support

For issues:
1. Check the USAGE_GUIDE.md
2. Review backend logs in terminal
3. Check browser console for frontend errors
4. Ensure template file exists and is accessible

## License

Private use for Andrew Morton / Capital Tech Alliance
