-- ============================================================================
-- Meeting Minutes Pro - Phase 1 Database Schema
-- PostgreSQL 15+ with advanced features
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For multi-column indexes

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table (for auth + multi-tenancy)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    meeting_type VARCHAR(100),  -- planning, retrospective, standup, etc.
    description TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    location VARCHAR(255),
    meeting_link TEXT,  -- Zoom, Teams, etc.
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled

    -- Ownership
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID,  -- For multi-tenancy (future)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED
);

-- Attendees table (many-to-many with meetings)
CREATE TABLE IF NOT EXISTS attendees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    attendance_status VARCHAR(50) DEFAULT 'invited',  -- invited, accepted, declined, attended
    is_required BOOLEAN DEFAULT FALSE,
    role VARCHAR(100),  -- presenter, note-taker, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(meeting_id, user_id)
);

-- Agenda items table
CREATE TABLE IF NOT EXISTS agenda_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    duration_minutes INTEGER,
    order_index INTEGER NOT NULL DEFAULT 0,
    presenter_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Action items table
CREATE TABLE IF NOT EXISTS action_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    due_date DATE,
    priority VARCHAR(50) DEFAULT 'medium',  -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, blocked, cancelled
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Meeting notes/minutes table
CREATE TABLE IF NOT EXISTS meeting_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT,
    notes_type VARCHAR(50) DEFAULT 'general',  -- general, decision, discussion, etc.
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(content, ''))
    ) STORED
);

-- Decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    decision_maker_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rationale TEXT,
    alternatives_considered JSONB,  -- Array of alternative options
    impact VARCHAR(50),  -- low, medium, high
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Attachments/Files table
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transcripts table (for AI transcription)
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    confidence_score DECIMAL(5,4),  -- 0.0000 to 1.0000
    transcript_segments JSONB,  -- Timestamped segments with speaker info
    ai_model VARCHAR(100),  -- whisper-large-v3, azure-stt, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(content, ''))
    ) STORED
);

-- AI Analysis table (for meeting insights)
CREATE TABLE IF NOT EXISTS ai_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,  -- summary, sentiment, topics, etc.
    results JSONB NOT NULL,
    ai_model VARCHAR(100),
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- REAL-TIME COLLABORATION TABLES
-- ============================================================================

-- WebSocket sessions (for presence tracking)
CREATE TABLE IF NOT EXISTS websocket_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB  -- Browser, IP, device info
);

-- Real-time edits (for collaborative editing)
CREATE TABLE IF NOT EXISTS realtime_edits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    edit_type VARCHAR(100) NOT NULL,  -- cursor_position, text_insert, text_delete, etc.
    content JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT & ANALYTICS TABLES
-- ============================================================================

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- CREATE, UPDATE, DELETE, VIEW
    resource_type VARCHAR(100) NOT NULL,  -- meeting, action_item, etc.
    resource_id UUID,
    changes JSONB,  -- Before/after values
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Meeting metrics (for analytics)
CREATE TABLE IF NOT EXISTS meeting_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,

    -- Time metrics
    actual_start_time TIMESTAMP WITH TIME ZONE,
    actual_end_time TIMESTAMP WITH TIME ZONE,
    actual_duration_minutes INTEGER,

    -- Participation metrics
    total_attendees INTEGER,
    active_participants INTEGER,
    speaking_time_distribution JSONB,  -- {user_id: minutes}

    -- Engagement metrics
    questions_asked INTEGER DEFAULT 0,
    decisions_made INTEGER DEFAULT 0,
    action_items_created INTEGER DEFAULT 0,

    -- Sentiment
    overall_sentiment DECIMAL(3,2),  -- -1.00 to 1.00
    sentiment_trend JSONB,  -- Time-series of sentiment

    -- Quality score
    meeting_quality_score INTEGER,  -- 0-100

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Meetings indexes
CREATE INDEX IF NOT EXISTS idx_meetings_created_by ON meetings(created_by);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled_at ON meetings(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_organization ON meetings(organization_id);
CREATE INDEX IF NOT EXISTS idx_meetings_search_vector ON meetings USING GIN(search_vector);

-- Attendees indexes
CREATE INDEX IF NOT EXISTS idx_attendees_meeting ON attendees(meeting_id);
CREATE INDEX IF NOT EXISTS idx_attendees_user ON attendees(user_id);
CREATE INDEX IF NOT EXISTS idx_attendees_status ON attendees(attendance_status);

-- Agenda items indexes
CREATE INDEX IF NOT EXISTS idx_agenda_meeting ON agenda_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_agenda_order ON agenda_items(meeting_id, order_index);

-- Action items indexes
CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_assigned ON action_items(assigned_to);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_due_date ON action_items(due_date);
CREATE INDEX IF NOT EXISTS idx_action_items_priority ON action_items(priority);

-- Meeting notes indexes
CREATE INDEX IF NOT EXISTS idx_notes_meeting ON meeting_notes(meeting_id);
CREATE INDEX IF NOT EXISTS idx_notes_author ON meeting_notes(author_id);
CREATE INDEX IF NOT EXISTS idx_notes_search_vector ON meeting_notes USING GIN(search_vector);

-- Decisions indexes
CREATE INDEX IF NOT EXISTS idx_decisions_meeting ON decisions(meeting_id);
CREATE INDEX IF NOT EXISTS idx_decisions_maker ON decisions(decision_maker_id);

-- Attachments indexes
CREATE INDEX IF NOT EXISTS idx_attachments_meeting ON attachments(meeting_id);
CREATE INDEX IF NOT EXISTS idx_attachments_uploaded_by ON attachments(uploaded_by);

-- Transcripts indexes
CREATE INDEX IF NOT EXISTS idx_transcripts_meeting ON transcripts(meeting_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_search_vector ON transcripts USING GIN(search_vector);

-- AI Analysis indexes
CREATE INDEX IF NOT EXISTS idx_ai_analysis_meeting ON ai_analysis(meeting_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_type ON ai_analysis(analysis_type);

-- WebSocket sessions indexes
CREATE INDEX IF NOT EXISTS idx_ws_sessions_user ON websocket_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ws_sessions_meeting ON websocket_sessions(meeting_id);
CREATE INDEX IF NOT EXISTS idx_ws_sessions_active ON websocket_sessions(is_active, last_heartbeat);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at);

-- Meeting metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_meeting ON meeting_metrics(meeting_id);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attendees_updated_at BEFORE UPDATE ON attendees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agenda_items_updated_at BEFORE UPDATE ON agenda_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_action_items_updated_at BEFORE UPDATE ON action_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_notes_updated_at BEFORE UPDATE ON meeting_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decisions_updated_at BEFORE UPDATE ON decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_metrics_updated_at BEFORE UPDATE ON meeting_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA (Optional - for testing)
-- ============================================================================

-- Create a demo admin user (password: admin123 - change in production!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (id, email, username, full_name, hashed_password, is_superuser)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@meetingspro.com',
    'admin',
    'Admin User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIABVdRW.i',  -- admin123
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create a demo regular user
INSERT INTO users (id, email, username, full_name, hashed_password, is_superuser)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'user@meetingspro.com',
    'demo_user',
    'Demo User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIABVdRW.i',  -- admin123
    FALSE
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
