import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, MeetingMinutes } from '../services/api'
import SmartMeetingUpload from '../components/SmartMeetingUpload'
import {
  Edit, Trash2, Download, Plus, Calendar, FileText,
  Search, Filter, SortAsc, SortDesc, Copy, MoreVertical,
  CheckCircle2, XCircle, Users, ListChecks, Upload
} from 'lucide-react'
import { format, parseISO } from 'date-fns'

export default function EnhancedMeetingList() {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState<MeetingMinutes[]>([])
  const [filteredMeetings, setFilteredMeetings] = useState<MeetingMinutes[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'name'>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedMeetings, setSelectedMeetings] = useState<Set<number>>(new Set())
  const [showActions, setShowActions] = useState<number | null>(null)

  useEffect(() => {
    loadMeetings()
  }, [])

  useEffect(() => {
    filterAndSortMeetings()
  }, [meetings, searchTerm, sortBy, sortOrder])

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

  const filterAndSortMeetings = () => {
    let filtered = [...meetings]

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(meeting =>
        meeting.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        meeting.meeting_purpose.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        const dateA = new Date(a.meeting_date).getTime()
        const dateB = new Date(b.meeting_date).getTime()
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA
      } else {
        const nameA = a.project_name.toLowerCase()
        const nameB = b.project_name.toLowerCase()
        return sortOrder === 'asc'
          ? nameA.localeCompare(nameB)
          : nameB.localeCompare(nameA)
      }
    })

    setFilteredMeetings(filtered)
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

  const handleBatchDelete = async () => {
    if (selectedMeetings.size === 0) return

    if (!window.confirm(`Delete ${selectedMeetings.size} meeting(s)?`)) {
      return
    }

    try {
      await Promise.all(
        Array.from(selectedMeetings).map(id => api.deleteMeeting(id))
      )
      setMeetings(meetings.filter(m => !selectedMeetings.has(m.id!)))
      setSelectedMeetings(new Set())
    } catch (err) {
      alert('Failed to delete meetings')
    }
  }

  const handleExport = async (id: number) => {
    try {
      await api.exportMeeting(id)
    } catch (err) {
      alert('Failed to export meeting')
    }
  }

  const handleDuplicate = async (meeting: MeetingMinutes) => {
    try {
      const duplicate: MeetingMinutes = {
        project_name: meeting.project_name + ' (Copy)',
        meeting_date: new Date().toISOString().split('T')[0],
        meeting_purpose: meeting.meeting_purpose,
        agenda_items: meeting.agenda_items,
        attendees: meeting.attendees,
        action_items: meeting.action_items.map(item => ({
          ...item,
          status: 'Pending'
        }))
      }
      const created = await api.createMeeting(duplicate)
      navigate(`/edit/${created.id}`)
    } catch (err) {
      alert('Failed to duplicate meeting')
    }
  }

  const toggleSelectMeeting = (id: number) => {
    const newSelected = new Set(selectedMeetings)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedMeetings(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedMeetings.size === filteredMeetings.length) {
      setSelectedMeetings(new Set())
    } else {
      setSelectedMeetings(new Set(filteredMeetings.map(m => m.id!)))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading meetings...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800 flex items-center gap-2">
          <XCircle className="h-5 w-5" />
          {error}
        </p>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Smart AI Upload Section */}
      <div className="mb-8">
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6 border border-purple-200/50 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <Upload className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Smart AI Upload</h3>
              <p className="text-sm text-gray-600">Just drop files - AI handles everything automatically</p>
            </div>
          </div>
          <SmartMeetingUpload />
        </div>
      </div>

      {/* Header */}
      <div className="mb-6 bg-white shadow-lg rounded-xl p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Meetings</h2>
            <p className="text-sm text-gray-600">
              {filteredMeetings.length} meeting{filteredMeetings.length !== 1 ? 's' : ''}
              {searchTerm && ` matching "${searchTerm}"`}
            </p>
          </div>
          <button
            onClick={() => navigate('/new')}
            className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all"
          >
            <Plus className="h-5 w-5 mr-2" />
            New Meeting
          </button>
        </div>

        {/* Search and Filter Bar */}
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search meetings by name or purpose..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setSortBy(sortBy === 'date' ? 'name' : 'date')}
              className="inline-flex items-center px-4 py-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <Filter className="h-4 w-4 mr-2" />
              {sortBy === 'date' ? 'Date' : 'Name'}
            </button>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="inline-flex items-center px-4 py-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? (
                <SortAsc className="h-4 w-4" />
              ) : (
                <SortDesc className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Batch Actions */}
        {selectedMeetings.size > 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedMeetings.size} meeting{selectedMeetings.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={handleBatchDelete}
                className="inline-flex items-center px-4 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Selected
              </button>
              <button
                onClick={() => setSelectedMeetings(new Set())}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Meetings List */}
      {filteredMeetings.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl shadow-lg">
          <FileText className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No meetings found' : 'No meetings yet'}
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            {searchTerm
              ? `No meetings match "${searchTerm}"`
              : 'Get started by creating your first meeting.'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => navigate('/new')}
              className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create First Meeting
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMeetings.map((meeting) => (
            <div
              key={meeting.id}
              className={`bg-white shadow-lg rounded-xl overflow-hidden transition-all hover:shadow-xl ${
                selectedMeetings.has(meeting.id!) ? 'ring-2 ring-blue-500' : ''
              }`}
            >
              <div className="p-6">
                <div className="flex items-start gap-4">
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedMeetings.has(meeting.id!)}
                    onChange={() => toggleSelectMeeting(meeting.id!)}
                    className="mt-1 h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                  />

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3
                          onClick={() => navigate(`/edit/${meeting.id}`)}
                          className="text-xl font-bold text-blue-600 hover:text-blue-800 cursor-pointer mb-1"
                        >
                          {meeting.project_name}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {format(parseISO(meeting.meeting_date), 'MMMM d, yyyy')}
                          </span>
                        </div>
                      </div>

                      {/* Action Menu */}
                      <div className="relative">
                        <button
                          onClick={() => setShowActions(showActions === meeting.id ? null : meeting.id!)}
                          className="p-2 hover:bg-gray-100 rounded-lg"
                        >
                          <MoreVertical className="h-5 w-5 text-gray-500" />
                        </button>

                        {showActions === meeting.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-10">
                            <button
                              onClick={() => {
                                navigate(`/edit/${meeting.id}`)
                                setShowActions(null)
                              }}
                              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                            >
                              <Edit className="h-4 w-4" />
                              Edit
                            </button>
                            <button
                              onClick={() => {
                                handleDuplicate(meeting)
                                setShowActions(null)
                              }}
                              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                            >
                              <Copy className="h-4 w-4" />
                              Duplicate
                            </button>
                            <button
                              onClick={() => {
                                handleExport(meeting.id!)
                                setShowActions(null)
                              }}
                              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                            >
                              <Download className="h-4 w-4" />
                              Export
                            </button>
                            <hr className="my-1" />
                            <button
                              onClick={() => {
                                handleDelete(meeting.id!)
                                setShowActions(null)
                              }}
                              className="w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 flex items-center gap-2"
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </div>

                    <p className="text-gray-700 mb-4 line-clamp-2">
                      {meeting.meeting_purpose}
                    </p>

                    {/* Stats */}
                    <div className="flex gap-6 text-sm">
                      <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-lg">
                        <ListChecks className="h-4 w-4 text-blue-600" />
                        <span className="text-blue-900 font-medium">
                          {meeting.agenda_items.length} agenda items
                        </span>
                      </div>

                      <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-lg">
                        <Users className="h-4 w-4 text-green-600" />
                        <span className="text-green-900 font-medium">
                          {meeting.attendees.filter(a => a.attended).length}/{meeting.attendees.length} attended
                        </span>
                      </div>

                      <div className="flex items-center gap-2 px-3 py-1 bg-purple-50 rounded-lg">
                        <CheckCircle2 className="h-4 w-4 text-purple-600" />
                        <span className="text-purple-900 font-medium">
                          {meeting.action_items.filter(a => a.status === 'Completed').length}/{meeting.action_items.length} completed
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
