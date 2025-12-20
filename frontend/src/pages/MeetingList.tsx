import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, MeetingMinutes } from '../services/api'
import { Edit, Trash2, Download, Plus, Calendar, FileText } from 'lucide-react'
import { format } from 'date-fns'

export default function MeetingList() {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState<MeetingMinutes[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMeetings()
  }, [])

  const loadMeetings = async () => {
    try {
      setLoading(true)
      const data = await api.getMeetings()
      setMeetings(data)
    } catch (err) {
      setError('Failed to load meetings')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this meeting?')) {
      return
    }

    try {
      await api.deleteMeeting(id)
      setMeetings(meetings.filter(m => m.id !== id))
    } catch (err) {
      alert('Failed to delete meeting')
    }
  }

  const handleExport = async (id: number) => {
    try {
      await api.exportMeeting(id)
    } catch (err) {
      alert('Failed to export meeting')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading meetings...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Meeting Minutes</h2>
        <button
          onClick={() => navigate('/new')}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Meeting
        </button>
      </div>

      {meetings.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No meetings</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new meeting.</p>
          <div className="mt-6">
            <button
              onClick={() => navigate('/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Meeting
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {meetings.map((meeting) => (
              <li key={meeting.id}>
                <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-medium text-blue-600 truncate">
                        {meeting.project_name}
                      </h3>
                      <div className="mt-2 flex items-center text-sm text-gray-500">
                        <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                        <span>
                          {format(new Date(meeting.meeting_date), 'MMMM d, yyyy')}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                        {meeting.meeting_purpose}
                      </p>
                      <div className="mt-2 flex gap-4 text-xs text-gray-500">
                        <span>{meeting.agenda_items.length} agenda items</span>
                        <span>{meeting.attendees.length} attendees</span>
                        <span>{meeting.action_items.length} action items</span>
                      </div>
                    </div>
                    <div className="ml-4 flex-shrink-0 flex space-x-2">
                      <button
                        onClick={() => navigate(`/edit/${meeting.id}`)}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                        title="Edit"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleExport(meeting.id!)}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                        title="Export to DOCX"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(meeting.id!)}
                        className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
