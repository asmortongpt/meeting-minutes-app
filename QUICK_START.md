# ⚡ Quick Start Guide - Meeting Minutes Pro

**Get running in 60 seconds** 🚀

---

## 🎯 Prerequisites

Make sure you have:
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 14+ (or use Docker)
- ✅ Redis 7+ (or use Docker)

---

## 🚀 Option 1: One-Command Start (Easiest)

```bash
# Start everything (PostgreSQL + Redis + Backend + Frontend)
./start-phase1.sh

# Wait 30 seconds for services to initialize...
# Browser opens automatically at http://localhost:5176
```

**That's it!** 🎉

---

## 🐳 Option 2: Docker Start (Production-like)

```bash
# Start databases only
docker-compose up -d postgres redis

# Start backend
cd backend-enhanced
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5176

---

## 🧪 Test Everything

```bash
# Run integration tests (22 tests)
./test-phase1-2.sh

# Expected output:
# ✅ Tests Passed: 22
# ❌ Tests Failed: 0
```

---

## 📝 Create Your First Meeting

### Via Web UI:
1. Open http://localhost:5176
2. Click "New Meeting"
3. Fill in details:
   - Title: "Project Kickoff"
   - Description: "Initial planning session"
4. Click "Start Recording"
5. Speak into microphone
6. Watch AI copilot extract action items in real-time! ✨

### Via API:
```bash
# Create meeting
curl -X POST http://localhost:8001/api/meetings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Kickoff",
    "description": "Initial planning",
    "organization_id": 1,
    "created_by": 1
  }'

# Start transcription
curl -X POST http://localhost:8001/api/transcription/start \
  -F "audio=@recording.wav" \
  -F "meeting_id=1"

# Start AI copilot
curl -X POST http://localhost:8001/api/copilot/start \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": 1,
    "agenda": ["Introductions", "Goals", "Next steps"]
  }'
```

---

## 🎨 What You Can Do

### 1. Real-time Collaboration
- Open same meeting in 2+ browsers
- Type in one → See updates in others instantly
- See who's viewing (presence indicators)
- Cursor positions, typing indicators

### 2. AI-Powered Features
- **Auto-transcription**: Upload audio → Get text with speakers
- **Action Items**: AI extracts "John will..." automatically
- **Smart Summary**: 3-bullet executive summary in 10 seconds
- **Blocker Detection**: Alerts when "blocked by..." is mentioned
- **Follow-up Email**: Professional email generated for you

### 3. Offline Mode (PWA)
- Install as app (click "Install" in browser)
- Works without internet
- Syncs when reconnected

---

## 📊 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5176 | Web UI |
| Backend API | http://localhost:8001 | REST API |
| API Docs | http://localhost:8001/docs | Interactive API documentation |
| PostgreSQL | localhost:5433 | Database (user: `meeting_user`) |
| Redis | localhost:6380 | Cache (no auth by default) |

---

## 🛑 Stop Services

```bash
# Stop everything gracefully
./stop-phase1.sh
```

---

## 🔧 Troubleshooting

### Problem: Port already in use

```bash
# Find what's using port 8001
lsof -i :8001

# Kill it
kill -9 <PID>

# Or use different ports in .env:
# BACKEND_PORT=8002
# FRONTEND_PORT=5177
```

### Problem: Database connection failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or start manually
docker run -d --name postgres \
  -e POSTGRES_USER=meeting_user \
  -e POSTGRES_PASSWORD=meeting_pass \
  -e POSTGRES_DB=meetings_db \
  -p 5433:5432 \
  postgres:14
```

### Problem: Redis connection failed

```bash
# Check Redis is running
docker ps | grep redis

# Or start manually
docker run -d --name redis -p 6380:6379 redis:7
```

### Problem: Frontend not loading

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Problem: AI features not working

```bash
# Check environment variables
cat .env | grep API_KEY

# Expected:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...

# If missing, add to .env and restart backend
```

---

## 📚 Next Steps

### Learn More:
- **Full Architecture**: Read `ARCHITECTURE.md`
- **Project Status**: Read `PROJECT_STATUS.md`
- **Phase Details**: Read `PHASE1_COMPLETE.md` and `PHASE2_COMPLETE.md`
- **API Reference**: Visit http://localhost:8001/docs

### Try Advanced Features:
1. **Upload Audio File**:
   - Go to http://localhost:5176/record
   - Click "Upload Audio"
   - Watch AI transcribe with speakers!

2. **Test Multi-Model AI**:
   - Go to API docs: http://localhost:8001/docs
   - Try `/api/ai/summarize` with different models
   - Compare Claude vs GPT-4 vs Gemini

3. **Real-time Collaboration**:
   - Open 2 browsers side-by-side
   - Edit same meeting in both
   - See instant updates!

4. **Meeting Copilot**:
   - Start a meeting
   - Begin recording
   - Watch AI extract action items live
   - Get time warnings when over limit
   - Receive quality score at end

---

## 🎓 Example Workflows

### Workflow 1: Team Standup (5 min)
```
1. Click "New Meeting" → "Daily Standup"
2. Click "Start Recording"
3. Each person speaks:
   - "Yesterday I completed the login feature"
   - "Today I'll work on the dashboard"
   - "No blockers"
4. Click "Stop Recording"
5. AI generates:
   ✅ Summary (3 bullets)
   ✅ Action items (auto-extracted)
   ✅ Follow-up email (ready to send)
```

### Workflow 2: Client Call (60 min)
```
1. Schedule meeting with client email
2. Prepare agenda in description
3. Start recording when call begins
4. AI copilot monitors in real-time:
   - Extracts decisions
   - Flags blockers
   - Alerts at 55 min (time warning)
5. End meeting → Get:
   ✅ Full transcript with speakers
   ✅ Executive summary
   ✅ Action items with owners
   ✅ Quality score (0-100)
   ✅ Professional follow-up email
```

### Workflow 3: Offline Meeting (Airport lounge)
```
1. Install PWA (one-time)
2. Open app (works offline!)
3. Record meeting locally
4. When online → Auto-sync to cloud
5. AI processes in background
6. Get notification when ready
```

---

## 💡 Pro Tips

### 🎯 Get Better AI Results:
- Speak clearly with 1-2 sec pauses
- Mention names: "John, can you..."
- Use action words: "will", "should", "must"
- State deadlines: "by Friday", "next week"

### ⚡ Performance:
- Close unused meetings (frees memory)
- Clear cache weekly (Settings → Cache)
- Use Chrome/Edge (best WebSocket support)

### 🔒 Security:
- Don't share API keys in meetings
- Use unique password per user
- Enable 2FA (Settings → Security) - Phase 6
- Review access logs monthly - Phase 6

---

## 🆘 Get Help

### Documentation:
- **Architecture**: `ARCHITECTURE.md`
- **Project Status**: `PROJECT_STATUS.md`
- **Phase Guides**: `PHASE1_COMPLETE.md`, `PHASE2_COMPLETE.md`

### Support:
- **Issues**: Create GitHub issue
- **Questions**: See FAQ in `docs/FAQ.md` (future)
- **Community**: Join Discord (future)

---

## 🎉 You're Ready!

Start the app:
```bash
./start-phase1.sh
```

Create your first meeting and experience the AI magic! ✨

---

*Built with ❤️ using Claude Code*
*Last updated: December 19, 2025*
