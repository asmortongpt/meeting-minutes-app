import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface AgendaItem {
  item: string;
  notes: string;
}

export interface Attendee {
  name: string;
  attended: boolean;
}

export interface ActionItem {
  description: string;
  owner: string;
  due_date?: string;
  status: string;
}

export interface MeetingMinutes {
  id?: number;
  project_name: string;
  meeting_date: string;
  meeting_purpose: string;
  agenda_items: AgendaItem[];
  attendees: Attendee[];
  action_items: ActionItem[];
  created_at?: string;
  updated_at?: string;
}

export const api = {
  // Basic CRUD operations
  getMeetings: async (): Promise<MeetingMinutes[]> => {
    const response = await axios.get(`${API_BASE_URL}/meetings`);
    return response.data;
  },

  getMeeting: async (id: number): Promise<MeetingMinutes> => {
    const response = await axios.get(`${API_BASE_URL}/meetings/${id}`);
    return response.data;
  },

  createMeeting: async (meeting: MeetingMinutes): Promise<MeetingMinutes> => {
    const response = await axios.post(`${API_BASE_URL}/meetings`, meeting);
    return response.data;
  },

  updateMeeting: async (id: number, meeting: MeetingMinutes): Promise<MeetingMinutes> => {
    const response = await axios.put(`${API_BASE_URL}/meetings/${id}`, meeting);
    return response.data;
  },

  deleteMeeting: async (id: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/meetings/${id}`);
  },

  exportMeeting: async (id: number): Promise<void> => {
    const response = await axios.get(`${API_BASE_URL}/meetings/${id}/export`, {
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `meeting_minutes_${id}.docx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // AI-powered features (optional, costs tokens)
  uploadScreenshot: async (file: File): Promise<{ file_path: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/screenshots/upload`, formData);
    return response.data;
  },

  analyzeScreenshot: async (filePath: string, context?: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/screenshots/analyze`, null, {
      params: { file_path: filePath, context },
    });
    return response.data;
  },

  identifySpeakers: async (filePath: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/screenshots/identify-speakers`, null, {
      params: { file_path: filePath },
    });
    return response.data;
  },

  generateMeetingMinutes: async (
    meetingNotes: string,
    screenshotPaths?: string[],
    additionalContext?: string
  ): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/meetings/ai-generate`, {
      meeting_notes: meetingNotes,
      screenshot_paths: screenshotPaths,
      additional_context: additionalContext,
    });
    return response.data;
  },
};
