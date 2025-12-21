import React, { useState, useCallback, useRef } from 'react';
import { Upload, FileAudio, FileVideo, Loader2, CheckCircle, XCircle, Sparkles, Users, Calendar, Tag, MessageSquare } from 'lucide-react';
import SmartInsightsPanel from './SmartInsightsPanel';

interface UploadedFile {
  file: File;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  analysis?: MeetingAnalysis;
  insights?: ProactiveInsight;
  error?: string;
}

interface MeetingAnalysis {
  title: string;
  date: string;
  duration: string;
  speakers: Array<{
    name: string;
    role?: string;
    speakingTime: number;
  }>;
  topics: string[];
  actionItems: Array<{
    task: string;
    assignee?: string;
    dueDate?: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  decisions: string[];
  summary: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  projectCategory?: string;
}

interface ProactiveInsight {
  smart_suggestions: any[];
  detected_risks: any[];
  follow_up_recommendations: any[];
  related_meetings: any[];
  pattern_insights: any[];
  proactive_alerts: any[];
}

const SmartMeetingUpload: React.FC = () => {
  const [files, setFiles] = useState<Map<string, UploadedFile>>(new Map());
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const generateProactiveInsights = async (): Promise<ProactiveInsight> => {
    // Simulate proactive intelligence generation
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      smart_suggestions: [
        {
          type: 'draft_email',
          priority: 'high',
          title: 'Send action item summary to team',
          auto_draft: `Subject: Action Items from Meeting\n\nHi Team,\n\nThank you for attending today's meeting. Here's a summary of action items:\n\n1. Complete infrastructure deployment by Friday - Mike Chen\n2. Review and approve budget proposal - Andrew Morton\n3. Schedule follow-up meeting - Sarah Johnson\n\nBest regards`,
          confidence: 0.85
        },
        {
          type: 'schedule_meeting',
          priority: 'medium',
          title: 'Schedule follow-up meeting',
          suggested_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          suggested_attendees: ['Andrew Morton', 'Sarah Johnson', 'Mike Chen'],
          confidence: 0.78
        }
      ],
      detected_risks: [
        {
          type: 'deadline_conflict',
          severity: 'high',
          message: 'Mike Chen has multiple tasks due within 24 hours',
          suggestion: 'Consider redistributing tasks or extending deadlines',
          tasks: ['Complete infrastructure deployment', 'Review code changes'],
          dates: ['2024-12-27', '2024-12-27']
        }
      ],
      follow_up_recommendations: [
        {
          type: 'overdue_action',
          priority: 'high',
          message: 'Overdue: Review budget proposal from last meeting',
          original_meeting: 'Q4 Planning Meeting',
          assignee: 'Andrew Morton',
          days_overdue: 2
        }
      ],
      related_meetings: [
        {
          meeting: { title: 'Q4 Budget Review', meeting_date: '2024-12-15' },
          score: 85,
          reasons: ['Same project', 'Shared attendees: Andrew Morton, Sarah Johnson']
        }
      ],
      pattern_insights: [
        {
          type: 'topic_trends',
          trending_up: ['API Development', 'Infrastructure'],
          trending_down: ['Budget', 'Marketing'],
          insight: 'Technical topics are becoming more discussed'
        },
        {
          type: 'completion_rate',
          rate: 72.5,
          insight: 'Team completes 72.5% of action items on time',
          benchmark: 'Industry average is 65%'
        },
        {
          type: 'effectiveness',
          score: 8.2,
          factors: {
            action_items_per_meeting: 4.2,
            decisions_per_meeting: 2.1,
            follow_through_rate: 72.5
          }
        }
      ],
      proactive_alerts: [
        {
          type: 'deadline_reminder',
          urgency: 'high',
          message: '2 action items due in next 48 hours',
          items: [
            { task: 'Review budget proposal', due_date: '2024-12-24' },
            { task: 'Complete infrastructure deployment', due_date: '2024-12-27' }
          ]
        }
      ]
    };
  };

  const analyzeFile = async (file: File): Promise<MeetingAnalysis> => {
    // Simulate AI analysis - in production, this would call the backend API
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Extract file metadata
    const fileName = file.name;
    const fileDate = new Date(file.lastModified);

    // Simulate AI-powered analysis
    return {
      title: `${fileName.replace(/\.[^/.]+$/, '')} - Meeting`,
      date: fileDate.toISOString(),
      duration: '45 minutes',
      speakers: [
        { name: 'Andrew Morton', role: 'Project Lead', speakingTime: 60 },
        { name: 'Sarah Johnson', role: 'Technical Director', speakingTime: 25 },
        { name: 'Mike Chen', role: 'Developer', speakingTime: 15 },
      ],
      topics: [
        'Project Timeline Review',
        'Budget Allocation',
        'Technical Architecture',
        'Resource Planning',
      ],
      actionItems: [
        {
          task: 'Complete infrastructure deployment by Friday',
          assignee: 'Mike Chen',
          dueDate: '2024-12-27',
          priority: 'high',
        },
        {
          task: 'Review and approve budget proposal',
          assignee: 'Andrew Morton',
          dueDate: '2024-12-24',
          priority: 'medium',
        },
        {
          task: 'Schedule follow-up meeting with stakeholders',
          assignee: 'Sarah Johnson',
          dueDate: '2024-12-26',
          priority: 'medium',
        },
      ],
      decisions: [
        'Approved Q1 budget increase of 15%',
        'Moved launch date to February 1st',
        'Adopted microservices architecture for backend',
      ],
      summary: 'Team discussed project progress and made key decisions regarding timeline and budget. All stakeholders aligned on the new February launch date. Technical architecture has been finalized with consensus on microservices approach.',
      sentiment: 'positive',
      projectCategory: 'Software Development',
    };
  };

  const processFile = async (file: File) => {
    const fileId = `${file.name}-${Date.now()}`;

    // Add file to state with uploading status
    setFiles(prev => new Map(prev).set(fileId, {
      file,
      status: 'uploading',
      progress: 0,
    }));

    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 20) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setFiles(prev => {
          const updated = new Map(prev);
          const fileData = updated.get(fileId);
          if (fileData) {
            updated.set(fileId, { ...fileData, progress: i });
          }
          return updated;
        });
      }

      // Change to processing status
      setFiles(prev => {
        const updated = new Map(prev);
        const fileData = updated.get(fileId);
        if (fileData) {
          updated.set(fileId, { ...fileData, status: 'processing', progress: 0 });
        }
        return updated;
      });

      // Analyze the file with AI
      const analysis = await analyzeFile(file);

      // Generate proactive insights
      const insights = await generateProactiveInsights();

      // Update with complete status, analysis, and insights
      setFiles(prev => {
        const updated = new Map(prev);
        const fileData = updated.get(fileId);
        if (fileData) {
          updated.set(fileId, {
            ...fileData,
            status: 'complete',
            progress: 100,
            analysis,
            insights,
          });
        }
        return updated;
      });

      // Auto-save to backend
      await saveMeetingToBackend(analysis, file);

    } catch (error) {
      setFiles(prev => {
        const updated = new Map(prev);
        const fileData = updated.get(fileId);
        if (fileData) {
          updated.set(fileId, {
            ...fileData,
            status: 'error',
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
        return updated;
      });
    }
  };

  const saveMeetingToBackend = async (analysis: MeetingAnalysis, file: File) => {
    // TODO: Call backend API to save meeting
    console.log('Saving meeting to backend:', analysis);
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    const audioVideoFiles = droppedFiles.filter(file =>
      file.type.startsWith('audio/') ||
      file.type.startsWith('video/') ||
      file.name.match(/\.(mp3|mp4|wav|m4a|webm|ogg|mov|avi)$/i)
    );

    for (const file of audioVideoFiles) {
      processFile(file);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      for (const file of selectedFiles) {
        processFile(file);
      }
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-300 group
          ${isDragging
            ? 'border-indigo-500 bg-indigo-50 scale-105'
            : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,video/*,.mp3,.mp4,.wav,.m4a,.webm,.ogg,.mov,.avi"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="space-y-4">
          <div className={`
            mx-auto w-16 h-16 rounded-full flex items-center justify-center
            transition-all duration-300
            ${isDragging
              ? 'bg-indigo-600 scale-110'
              : 'bg-gradient-to-br from-purple-500 to-indigo-600 group-hover:scale-110'
            }
          `}>
            <Upload className="w-8 h-8 text-white" />
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Drop Meeting Files Here
            </h3>
            <p className="text-gray-600 mb-4">
              or click to browse for audio/video files
            </p>
            <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <FileAudio className="w-4 h-4" />
                MP3, WAV, M4A
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <FileVideo className="w-4 h-4" />
                MP4, MOV, WebM
              </span>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-sm font-medium text-indigo-600">
            <Sparkles className="w-4 h-4" />
            AI will automatically analyze everything
          </div>
        </div>
      </div>

      {/* Processing Files */}
      {files.size > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Processing Files</h3>

          {Array.from(files.entries()).map(([id, fileData]) => (
            <div key={id} className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
              {/* File Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {fileData.file.type.startsWith('audio/') ? (
                    <FileAudio className="w-8 h-8 text-purple-600" />
                  ) : (
                    <FileVideo className="w-8 h-8 text-indigo-600" />
                  )}
                  <div>
                    <h4 className="font-medium text-gray-900">{fileData.file.name}</h4>
                    <p className="text-sm text-gray-500">
                      {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {fileData.status === 'complete' && (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                )}
                {fileData.status === 'error' && (
                  <XCircle className="w-6 h-6 text-red-600" />
                )}
                {(fileData.status === 'uploading' || fileData.status === 'processing') && (
                  <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
                )}
              </div>

              {/* Progress Bar */}
              {(fileData.status === 'uploading' || fileData.status === 'processing') && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>
                      {fileData.status === 'uploading' ? 'Uploading...' : 'Analyzing with AI...'}
                    </span>
                    <span>{fileData.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-purple-600 to-indigo-600 h-full transition-all duration-300"
                      style={{ width: `${fileData.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Analysis Results */}
              {fileData.status === 'complete' && fileData.analysis && (
                <div className="space-y-4 pt-4 border-t border-gray-200">
                  {/* Meeting Title & Summary */}
                  <div>
                    <h5 className="font-semibold text-gray-900 mb-2">{fileData.analysis.title}</h5>
                    <p className="text-sm text-gray-600">{fileData.analysis.summary}</p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">
                        {new Date(fileData.analysis.date).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">
                        {fileData.analysis.speakers.length} speakers
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">{fileData.analysis.duration}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Tag className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">{fileData.analysis.projectCategory}</span>
                    </div>
                  </div>

                  {/* Speakers */}
                  <div>
                    <h6 className="text-sm font-semibold text-gray-700 mb-2">Identified Speakers</h6>
                    <div className="flex flex-wrap gap-2">
                      {fileData.analysis.speakers.map((speaker, idx) => (
                        <div
                          key={idx}
                          className="px-3 py-1.5 bg-purple-50 border border-purple-200 rounded-lg text-sm"
                        >
                          <span className="font-medium text-purple-900">{speaker.name}</span>
                          {speaker.role && (
                            <span className="text-purple-600 ml-1">• {speaker.role}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Items */}
                  <div>
                    <h6 className="text-sm font-semibold text-gray-700 mb-2">
                      Action Items ({fileData.analysis.actionItems.length})
                    </h6>
                    <div className="space-y-2">
                      {fileData.analysis.actionItems.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-sm p-2 bg-amber-50 border border-amber-200 rounded"
                        >
                          <div className={`
                            w-2 h-2 rounded-full mt-1.5
                            ${item.priority === 'high' ? 'bg-red-500' :
                              item.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'}
                          `} />
                          <div className="flex-1">
                            <p className="text-gray-900">{item.task}</p>
                            <p className="text-gray-600 text-xs mt-1">
                              {item.assignee && `Assignee: ${item.assignee}`}
                              {item.dueDate && ` • Due: ${new Date(item.dueDate).toLocaleDateString()}`}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* AI Insights Panel */}
              {fileData.status === 'complete' && fileData.insights && (
                <SmartInsightsPanel insights={fileData.insights} />
              )}

              {/* Error */}
              {fileData.status === 'error' && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  Error: {fileData.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SmartMeetingUpload;
