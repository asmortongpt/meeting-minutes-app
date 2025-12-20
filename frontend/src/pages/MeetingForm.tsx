import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, MeetingMinutes, AgendaItem, Attendee, ActionItem } from '../services/api'
import { Save, Upload, Sparkles, Plus, Trash2, X, AlertCircle } from 'lucide-react'
import { useDropzone } from 'react-dropzone'

export default function MeetingForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEditing = !!id

  const [projectName, setProjectName] = useState('')
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().split('T')[0])
  const [meetingPurpose, setMeetingPurpose] = useState('')
  const [agendaItems, setAgendaItems] = useState<AgendaItem[]>([{ item: '', notes: '' }])
  const [attendees, setAttendees] = useState<Attendee[]>([{ name: '', attended: true }])
  const [actionItems, setActionItems] = useState<ActionItem[]>([
    { description: '', owner: '', due_date: '', status: 'Pending' }
  ])

  const [meetingNotes, setMeetingNotes] = useState('')
  const [uploadedScreenshots, setUploadedScreenshots] = useState<Array<{ path: string; filename: string }>>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showAIHelper, setShowAIHelper] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (isEditing && id) {
      loadMeeting(parseInt(id))
    }
  }, [id])

  const loadMeeting = async (meetingId: number) => {
    try {
      const meeting = await api.getMeeting(meetingId)
      setProjectName(meeting.project_name)
      setMeetingDate(meeting.meeting_date)
      setMeetingPurpose(meeting.meeting_purpose)
      setAgendaItems(meeting.agenda_items.length ? meeting.agenda_items : [{ item: '', notes: '' }])
      setAttendees(meeting.attendees.length ? meeting.attendees : [{ name: '', attended: true }])
      setActionItems(meeting.action_items.length ? meeting.action_items : [
        { description: '', owner: '', due_date: '', status: 'Pending' }
      ])
    } catch (err) {
      setError('Failed to load meeting')
    }
  }

  const onDrop = async (acceptedFiles: File[]) => {
    try {
      for (const file of acceptedFiles) {
        const result = await api.uploadScreenshot(file)
        setUploadedScreenshots(prev => [...prev, result])
      }
      setSuccess(`Uploaded ${acceptedFiles.length} screenshot(s)`)
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError('Failed to upload screenshots')
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg']
    }
  })

  const handleAIGenerate = async () => {
    if (!meetingNotes.trim()) {
      setError('Please enter meeting notes before using AI generation')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      const screenshotPaths = uploadedScreenshots.map(s => s.path)
      const result = await api.generateMeetingMinutes(
        meetingNotes,
        screenshotPaths.length ? screenshotPaths : undefined
      )

      if (result.success && result.analysis) {
        const analysis = result.analysis

        if (analysis.meeting_purpose) {
          setMeetingPurpose(analysis.meeting_purpose)
        }

        if (analysis.agenda_items && analysis.agenda_items.length) {
          setAgendaItems(analysis.agenda_items)
        }

        if (analysis.attendees && analysis.attendees.length) {
          setAttendees(analysis.attendees)
        }

        if (analysis.action_items && analysis.action_items.length) {
          setActionItems(analysis.action_items)
        }

        setSuccess('AI analysis complete! Review and adjust the generated content.')
        setShowAIHelper(false)
      } else {
        setError('AI generation failed: ' + (result.error || 'Unknown error'))
      }
    } catch (err: any) {
      setError('AI generation failed: ' + (err.message || 'Unknown error'))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSave = async () => {
    setError(null)
    setIsSaving(true)

    try {
      const meeting: MeetingMinutes = {
        project_name: projectName,
        meeting_date: meetingDate,
        meeting_purpose: meetingPurpose,
        agenda_items: agendaItems.filter(item => item.item.trim() || item.notes.trim()),
        attendees: attendees.filter(att => att.name.trim()),
        action_items: actionItems.filter(item => item.description.trim())
      }

      if (isEditing && id) {
        await api.updateMeeting(parseInt(id), meeting)
        setSuccess('Meeting updated successfully!')
      } else {
        const created = await api.createMeeting(meeting)
        setSuccess('Meeting created successfully!')
        setTimeout(() => navigate(`/edit/${created.id}`), 1500)
      }
    } catch (err: any) {
      setError('Failed to save meeting: ' + (err.message || 'Unknown error'))
    } finally {
      setIsSaving(false)
    }
  }

  const addAgendaItem = () => {
    setAgendaItems([...agendaItems, { item: '', notes: '' }])
  }

  const removeAgendaItem = (index: number) => {
    setAgendaItems(agendaItems.filter((_, i) => i !== index))
  }

  const addAttendee = () => {
    setAttendees([...attendees, { name: '', attended: true }])
  }

  const removeAttendee = (index: number) => {
    setAttendees(attendees.filter((_, i) => i !== index))
  }

  const addActionItem = () => {
    setActionItems([...actionItems, { description: '', owner: '', due_date: '', status: 'Pending' }])
  }

  const removeActionItem = (index: number) => {
    setActionItems(actionItems.filter((_, i) => i !== index))
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {isEditing ? 'Edit Meeting Minutes' : 'Create New Meeting Minutes'}
          </h2>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
              <span className="text-sm text-red-800">{error}</span>
              <button onClick={() => setError(null)} className="ml-auto">
                <X className="h-4 w-4 text-red-500" />
              </button>
            </div>
          )}

          {success && (
            <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4 flex items-start">
              <span className="text-sm text-green-800">{success}</span>
              <button onClick={() => setSuccess(null)} className="ml-auto">
                <X className="h-4 w-4 text-green-500" />
              </button>
            </div>
          )}

          {/* AI Helper Toggle */}
          <div className="mb-6">
            <button
              onClick={() => setShowAIHelper(!showAIHelper)}
              className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md shadow-sm text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {showAIHelper ? 'Hide AI Assistant' : 'Use AI Assistant (Optional)'}
            </button>
          </div>

          {showAIHelper && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                AI-Powered Meeting Analysis (Costs Tokens - Use Sparingly)
              </h3>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Meeting Notes / Transcript
                </label>
                <textarea
                  value={meetingNotes}
                  onChange={(e) => setMeetingNotes(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Paste your meeting notes or transcript here..."
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Screenshots (Optional)
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer ${
                    isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    {isDragActive ? 'Drop screenshots here...' : 'Drag & drop screenshots, or click to select'}
                  </p>
                </div>

                {uploadedScreenshots.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {uploadedScreenshots.map((screenshot, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
                        <span className="text-sm text-gray-600">{screenshot.filename}</span>
                        <button
                          onClick={() => setUploadedScreenshots(uploadedScreenshots.filter((_, i) => i !== index))}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={handleAIGenerate}
                disabled={isGenerating || !meetingNotes.trim()}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                {isGenerating ? 'Generating with AI...' : 'Generate Meeting Minutes with AI'}
              </button>
            </div>
          )}

          {/* Basic Information */}
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Name *
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meeting Date *
              </label>
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meeting Purpose *
              </label>
              <textarea
                value={meetingPurpose}
                onChange={(e) => setMeetingPurpose(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>

          {/* Agenda Items */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-medium text-gray-700">Agenda Items</label>
              <button
                onClick={addAgendaItem}
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Item
              </button>
            </div>
            <div className="space-y-3">
              {agendaItems.map((item, index) => (
                <div key={index} className="flex gap-3 items-start">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={item.item}
                      onChange={(e) => {
                        const updated = [...agendaItems]
                        updated[index].item = e.target.value
                        setAgendaItems(updated)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Agenda item"
                    />
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      value={item.notes}
                      onChange={(e) => {
                        const updated = [...agendaItems]
                        updated[index].notes = e.target.value
                        setAgendaItems(updated)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Notes"
                    />
                  </div>
                  <button
                    onClick={() => removeAgendaItem(index)}
                    className="mt-2 text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Attendees */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-medium text-gray-700">Attendees</label>
              <button
                onClick={addAttendee}
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Attendee
              </button>
            </div>
            <div className="space-y-3">
              {attendees.map((attendee, index) => (
                <div key={index} className="flex gap-3 items-center">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={attendee.name}
                      onChange={(e) => {
                        const updated = [...attendees]
                        updated[index].name = e.target.value
                        setAttendees(updated)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Name"
                    />
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={attendee.attended}
                      onChange={(e) => {
                        const updated = [...attendees]
                        updated[index].attended = e.target.checked
                        setAttendees(updated)
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">Attended</span>
                  </label>
                  <button
                    onClick={() => removeAttendee(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Action Items */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-medium text-gray-700">Action Items</label>
              <button
                onClick={addActionItem}
                className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Action Item
              </button>
            </div>
            <div className="space-y-3">
              {actionItems.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="col-span-2">
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => {
                          const updated = [...actionItems]
                          updated[index].description = e.target.value
                          setActionItems(updated)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Description"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={item.owner}
                        onChange={(e) => {
                          const updated = [...actionItems]
                          updated[index].owner = e.target.value
                          setActionItems(updated)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Owner"
                      />
                    </div>
                    <div>
                      <input
                        type="date"
                        value={item.due_date || ''}
                        onChange={(e) => {
                          const updated = [...actionItems]
                          updated[index].due_date = e.target.value
                          setActionItems(updated)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <select
                        value={item.status}
                        onChange={(e) => {
                          const updated = [...actionItems]
                          updated[index].status = e.target.value
                          setActionItems(updated)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="Blocked">Blocked</option>
                      </select>
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={() => removeActionItem(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !projectName || !meetingDate || !meetingPurpose}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : (isEditing ? 'Update Meeting' : 'Create Meeting')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
