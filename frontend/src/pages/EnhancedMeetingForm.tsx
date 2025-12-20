import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, MeetingMinutes, AgendaItem, Attendee, ActionItem } from '../services/api'
import {
  Save, Upload, Sparkles, Plus, X, AlertCircle,
  Copy, FileText, Calendar, Users, ListChecks,
  Download, Clock, CheckCircle2
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import DraggableAgendaItem from '../components/DraggableAgendaItem'
import DraggableAttendee from '../components/DraggableAttendee'
import DraggableActionItem from '../components/DraggableActionItem'
import VoiceInput from '../components/VoiceInput'
import QuickStart from '../components/QuickStart'

export default function EnhancedMeetingForm() {
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
  const [autoSaveStatus, setAutoSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved')

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    if (isEditing && id) {
      loadMeeting(parseInt(id))
    }
  }, [id])

  // Auto-save functionality
  useEffect(() => {
    if (!isEditing || !id) return

    const timer = setTimeout(() => {
      if (projectName && meetingDate && meetingPurpose) {
        handleAutoSave()
      }
    }, 2000)

    return () => clearTimeout(timer)
  }, [projectName, meetingDate, meetingPurpose, agendaItems, attendees, actionItems])

  const handleAutoSave = async () => {
    if (!id) return

    setAutoSaveStatus('saving')
    try {
      const meeting: MeetingMinutes = {
        project_name: projectName,
        meeting_date: meetingDate,
        meeting_purpose: meetingPurpose,
        agenda_items: agendaItems.filter(item => item.item.trim() || item.notes.trim()),
        attendees: attendees.filter(att => att.name.trim()),
        action_items: actionItems.filter(item => item.description.trim())
      }
      await api.updateMeeting(parseInt(id), meeting)
      setAutoSaveStatus('saved')
    } catch (err) {
      setAutoSaveStatus('unsaved')
    }
  }

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
        setAutoSaveStatus('saved')
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

  const handleDuplicateMeeting = async () => {
    if (!id) return

    try {
      const meeting: MeetingMinutes = {
        project_name: projectName + ' (Copy)',
        meeting_date: new Date().toISOString().split('T')[0],
        meeting_purpose: meetingPurpose,
        agenda_items: agendaItems.filter(item => item.item.trim() || item.notes.trim()),
        attendees: attendees.filter(att => att.name.trim()),
        action_items: actionItems.filter(item => item.description.trim()).map(item => ({
          ...item,
          status: 'Pending'
        }))
      }

      const created = await api.createMeeting(meeting)
      setSuccess('Meeting duplicated!')
      setTimeout(() => navigate(`/edit/${created.id}`), 1000)
    } catch (err) {
      setError('Failed to duplicate meeting')
    }
  }

  const handleExport = async () => {
    if (!id) {
      setError('Please save the meeting first')
      return
    }

    try {
      await api.exportMeeting(parseInt(id))
      setSuccess('Meeting exported to DOCX!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError('Failed to export meeting')
    }
  }

  // Drag and drop handlers
  const handleAgendaDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      setAgendaItems((items) => {
        const oldIndex = items.findIndex((_, i) => `agenda-${i}` === active.id)
        const newIndex = items.findIndex((_, i) => `agenda-${i}` === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  const handleAttendeesDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      setAttendees((items) => {
        const oldIndex = items.findIndex((_, i) => `attendee-${i}` === active.id)
        const newIndex = items.findIndex((_, i) => `attendee-${i}` === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  const handleActionsDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      setActionItems((items) => {
        const oldIndex = items.findIndex((_, i) => `action-${i}` === active.id)
        const newIndex = items.findIndex((_, i) => `action-${i}` === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow-lg rounded-xl">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                {isEditing ? 'Edit Meeting Minutes' : 'Create New Meeting Minutes'}
              </h2>
              <p className="text-sm text-gray-600">
                Drag and drop to reorder items • Auto-saves as you type
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isEditing && (
                <>
                  <div className="flex items-center gap-2 text-sm">
                    {autoSaveStatus === 'saved' && (
                      <span className="flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        Saved
                      </span>
                    )}
                    {autoSaveStatus === 'saving' && (
                      <span className="flex items-center gap-1 text-blue-600">
                        <Clock className="h-4 w-4 animate-spin" />
                        Saving...
                      </span>
                    )}
                  </div>
                  <button
                    onClick={handleDuplicateMeeting}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Duplicate
                  </button>
                  <button
                    onClick={handleExport}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          {/* Alerts */}
          {error && (
            <div className="mb-6 bg-red-50 border-l-4 border-red-400 rounded-md p-4 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-400 mr-3 mt-0.5" />
              <div className="flex-1">
                <span className="text-sm text-red-800">{error}</span>
              </div>
              <button onClick={() => setError(null)} className="ml-auto">
                <X className="h-5 w-5 text-red-500 hover:text-red-700" />
              </button>
            </div>
          )}

          {success && (
            <div className="mb-6 bg-green-50 border-l-4 border-green-400 rounded-md p-4 flex items-start">
              <CheckCircle2 className="h-5 w-5 text-green-400 mr-3 mt-0.5" />
              <div className="flex-1">
                <span className="text-sm text-green-800">{success}</span>
              </div>
              <button onClick={() => setSuccess(null)} className="ml-auto">
                <X className="h-5 w-5 text-green-500 hover:text-green-700" />
              </button>
            </div>
          )}

          {/* Quick Start - No Typing Required */}
          {!isEditing && (
            <QuickStart
              onSelect={(data) => {
                if (data.project_name) setProjectName(data.project_name)
                if (data.meeting_date) setMeetingDate(data.meeting_date)
                if (data.meeting_purpose) setMeetingPurpose(data.meeting_purpose)
                if (data.agenda_items) setAgendaItems(data.agenda_items)
                if (data.attendees) setAttendees(data.attendees)
                if (data.action_items) setActionItems(data.action_items)
              }}
            />
          )}

          {/* AI Helper Toggle */}
          <div className="mb-6">
            <button
              onClick={() => setShowAIHelper(!showAIHelper)}
              className="inline-flex items-center px-4 py-2 border-2 border-blue-300 rounded-lg shadow-sm text-sm font-medium text-blue-700 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 transition-all"
            >
              <Sparkles className="h-5 w-5 mr-2" />
              {showAIHelper ? 'Hide AI Assistant' : 'Use AI Assistant (Optional)'}
            </button>
          </div>

          {/* AI Helper Section */}
          {showAIHelper && (
            <div className="mb-8 p-6 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-xl shadow-inner">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-blue-600" />
                AI-Powered Meeting Analysis
                <span className="text-xs font-normal text-gray-600 bg-yellow-100 px-2 py-1 rounded">
                  Uses Tokens
                </span>
              </h3>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Meeting Notes / Transcript
                </label>
                <textarea
                  value={meetingNotes}
                  onChange={(e) => setMeetingNotes(e.target.value)}
                  rows={8}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  placeholder="Paste your meeting notes, transcript, or summary here...

Example:
Meeting with development team to discuss Q1 priorities.

Attendees: John Smith (PM), Sarah Johnson (Dev Lead), Mike Chen (Designer)

Discussion:
1. Frontend redesign - Sarah will lead, due Feb 15
2. API performance improvements - Mike to investigate
3. User testing sessions - John to schedule"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Screenshots (Optional)
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                    isDragActive
                      ? 'border-blue-500 bg-blue-50 scale-105'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                  <p className="text-sm font-medium text-gray-700 mb-1">
                    {isDragActive ? 'Drop screenshots here...' : 'Drag & drop screenshots, or click to select'}
                  </p>
                  <p className="text-xs text-gray-500">PNG, JPG, JPEG supported</p>
                </div>

                {uploadedScreenshots.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium text-gray-700">
                      {uploadedScreenshots.length} screenshot(s) uploaded
                    </p>
                    {uploadedScreenshots.map((screenshot, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
                        <span className="text-sm text-gray-600 flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          {screenshot.filename}
                        </span>
                        <button
                          onClick={() => setUploadedScreenshots(uploadedScreenshots.filter((_, i) => i !== index))}
                          className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded"
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
                className="w-full inline-flex justify-center items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all"
              >
                <Sparkles className="h-5 w-5 mr-2" />
                {isGenerating ? 'Generating with AI...' : 'Generate Meeting Minutes with AI'}
              </button>
            </div>
          )}

          {/* Basic Information */}
          <div className="mb-8 space-y-5">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 border-b pb-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Basic Information
            </h3>

            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name <span className="text-red-500">*</span>
                  <span className="ml-2 text-xs text-blue-600">(Voice input available)</span>
                </label>
                <VoiceInput
                  value={projectName}
                  onChange={setProjectName}
                  placeholder="e.g., Q1 Planning Meeting"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Meeting Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={meetingDate}
                  onChange={(e) => setMeetingDate(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meeting Purpose <span className="text-red-500">*</span>
                <span className="ml-2 text-xs text-blue-600">(Voice input available)</span>
              </label>
              <VoiceInput
                value={meetingPurpose}
                onChange={setMeetingPurpose}
                placeholder="Brief description of the meeting's objective..."
                multiline={true}
                rows={3}
              />
            </div>
          </div>

          {/* Agenda Items with Drag and Drop */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <ListChecks className="h-5 w-5 text-blue-600" />
                Agenda Items
                <span className="text-sm font-normal text-gray-500">
                  ({agendaItems.length})
                </span>
              </h3>
              <button
                onClick={() => setAgendaItems([...agendaItems, { item: '', notes: '' }])}
                className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Item
              </button>
            </div>

            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleAgendaDragEnd}
            >
              <SortableContext
                items={agendaItems.map((_, i) => `agenda-${i}`)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {agendaItems.map((item, index) => (
                    <DraggableAgendaItem
                      key={`agenda-${index}`}
                      id={`agenda-${index}`}
                      item={item}
                      index={index}
                      onUpdate={(idx, field, value) => {
                        const updated = [...agendaItems]
                        updated[idx][field] = value
                        setAgendaItems(updated)
                      }}
                      onRemove={(idx) => setAgendaItems(agendaItems.filter((_, i) => i !== idx))}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>

          {/* Attendees with Drag and Drop */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                Attendees
                <span className="text-sm font-normal text-gray-500">
                  ({attendees.filter(a => a.attended).length}/{attendees.length} attended)
                </span>
              </h3>
              <button
                onClick={() => setAttendees([...attendees, { name: '', attended: true }])}
                className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Attendee
              </button>
            </div>

            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleAttendeesDragEnd}
            >
              <SortableContext
                items={attendees.map((_, i) => `attendee-${i}`)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {attendees.map((attendee, index) => (
                    <DraggableAttendee
                      key={`attendee-${index}`}
                      id={`attendee-${index}`}
                      attendee={attendee}
                      index={index}
                      onUpdate={(idx, field, value) => {
                        const updated = [...attendees]
                        updated[idx][field] = value
                        setAttendees(updated)
                      }}
                      onRemove={(idx) => setAttendees(attendees.filter((_, i) => i !== idx))}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>

          {/* Action Items with Drag and Drop */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <ListChecks className="h-5 w-5 text-blue-600" />
                Action Items
                <span className="text-sm font-normal text-gray-500">
                  ({actionItems.filter(a => a.status === 'Completed').length}/{actionItems.length} completed)
                </span>
              </h3>
              <button
                onClick={() => setActionItems([...actionItems, { description: '', owner: '', due_date: '', status: 'Pending' }])}
                className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Action Item
              </button>
            </div>

            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleActionsDragEnd}
            >
              <SortableContext
                items={actionItems.map((_, i) => `action-${i}`)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {actionItems.map((item, index) => (
                    <DraggableActionItem
                      key={`action-${index}`}
                      id={`action-${index}`}
                      item={item}
                      index={index}
                      onUpdate={(idx, field, value) => {
                        const updated = [...actionItems]
                        updated[idx][field] = value
                        setActionItems(updated)
                      }}
                      onRemove={(idx) => setActionItems(actionItems.filter((_, i) => i !== idx))}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-6 border-t">
            <button
              onClick={() => navigate('/')}
              className="px-6 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !projectName || !meetingDate || !meetingPurpose}
              className="inline-flex items-center px-8 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all"
            >
              <Save className="h-5 w-5 mr-2" />
              {isSaving ? 'Saving...' : (isEditing ? 'Update Meeting' : 'Create Meeting')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
