import { useState } from 'react';
import { Sparkles, FileText, Users, Calendar, Clock, Clipboard, Check } from 'lucide-react';
import { MeetingMinutes } from '../services/api';

interface Props {
  onSelect: (data: Partial<MeetingMinutes>) => void;
}

const templates = [
  {
    id: 'standup',
    name: 'Daily Standup',
    icon: Clock,
    color: 'blue',
    data: {
      meeting_purpose: 'Daily team standup to discuss progress, blockers, and plans for the day',
      agenda_items: [
        { item: 'Yesterday\'s accomplishments', notes: 'What did each team member complete?' },
        { item: 'Today\'s plans', notes: 'What will each team member work on?' },
        { item: 'Blockers and challenges', notes: 'Any impediments to progress?' }
      ],
      action_items: []
    }
  },
  {
    id: 'planning',
    name: 'Sprint Planning',
    icon: Calendar,
    color: 'green',
    data: {
      meeting_purpose: 'Plan the upcoming sprint, review backlog, and assign tasks',
      agenda_items: [
        { item: 'Review sprint goal', notes: 'Define clear objectives for the sprint' },
        { item: 'Story refinement', notes: 'Review and estimate user stories' },
        { item: 'Capacity planning', notes: 'Confirm team availability and commitments' },
        { item: 'Task assignment', notes: 'Assign stories to team members' }
      ],
      action_items: []
    }
  },
  {
    id: 'retrospective',
    name: 'Retrospective',
    icon: Users,
    color: 'purple',
    data: {
      meeting_purpose: 'Reflect on the past sprint and identify improvements',
      agenda_items: [
        { item: 'What went well?', notes: 'Celebrate successes and effective practices' },
        { item: 'What could be improved?', notes: 'Identify challenges and pain points' },
        { item: 'Action items', notes: 'Define concrete improvements for next sprint' }
      ],
      action_items: []
    }
  },
  {
    id: 'client',
    name: 'Client Meeting',
    icon: FileText,
    color: 'indigo',
    data: {
      meeting_purpose: 'Review project progress and discuss client feedback',
      agenda_items: [
        { item: 'Project status update', notes: 'Current progress and milestones achieved' },
        { item: 'Demo and feedback', notes: 'Show completed features and gather input' },
        { item: 'Next steps', notes: 'Upcoming deliverables and timeline' },
        { item: 'Budget and resources', notes: 'Review costs and resource allocation' }
      ],
      action_items: []
    }
  }
];

export default function QuickStart({ onSelect }: Props) {
  const [copiedFromClipboard, setCopiedFromClipboard] = useState(false);

  const handleTemplateSelect = (template: typeof templates[0]) => {
    onSelect({
      project_name: `${template.name} - ${new Date().toLocaleDateString()}`,
      meeting_date: new Date().toISOString().split('T')[0],
      ...template.data
    });
  };

  const handleClipboardImport = async () => {
    try {
      const text = await navigator.clipboard.readText();

      if (!text.trim()) {
        alert('Clipboard is empty');
        return;
      }

      // Parse clipboard content
      const lines = text.split('\n').filter(line => line.trim());

      // Try to extract meeting info
      let purpose = '';
      const agendaItems: any[] = [];
      const attendees: any[] = [];
      const actionItems: any[] = [];

      let currentSection = '';

      for (const line of lines) {
        const lower = line.toLowerCase();

        if (lower.includes('purpose') || lower.includes('objective')) {
          currentSection = 'purpose';
          continue;
        } else if (lower.includes('agenda') || lower.includes('topics')) {
          currentSection = 'agenda';
          continue;
        } else if (lower.includes('attendees') || lower.includes('participants')) {
          currentSection = 'attendees';
          continue;
        } else if (lower.includes('action') || lower.includes('tasks') || lower.includes('todo')) {
          currentSection = 'actions';
          continue;
        }

        const trimmed = line.trim().replace(/^[-*•]\s*/, '');

        if (currentSection === 'purpose' && trimmed) {
          purpose += (purpose ? ' ' : '') + trimmed;
        } else if (currentSection === 'agenda' && trimmed) {
          agendaItems.push({ item: trimmed, notes: '' });
        } else if (currentSection === 'attendees' && trimmed) {
          attendees.push({ name: trimmed, attended: true });
        } else if (currentSection === 'actions' && trimmed) {
          actionItems.push({
            description: trimmed,
            owner: '',
            due_date: '',
            status: 'Pending'
          });
        }
      }

      onSelect({
        project_name: 'Imported Meeting - ' + new Date().toLocaleDateString(),
        meeting_date: new Date().toISOString().split('T')[0],
        meeting_purpose: purpose || text.substring(0, 200),
        agenda_items: agendaItems.length > 0 ? agendaItems : [{ item: '', notes: '' }],
        attendees: attendees.length > 0 ? attendees : [{ name: '', attended: true }],
        action_items: actionItems.length > 0 ? actionItems : [{ description: '', owner: '', due_date: '', status: 'Pending' }]
      });

      setCopiedFromClipboard(true);
      setTimeout(() => setCopiedFromClipboard(false), 3000);
    } catch (err) {
      alert('Failed to read from clipboard. Please make sure you\'ve granted permission.');
    }
  };

  return (
    <div className="mb-8 p-6 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-xl">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Sparkles className="h-6 w-6 text-blue-600" />
        Quick Start - No Typing Required!
      </h3>

      <p className="text-sm text-gray-600 mb-6">
        Choose a template or import from clipboard to get started instantly
      </p>

      {/* Templates */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {templates.map((template) => {
          const Icon = template.icon;
          return (
            <button
              key={template.id}
              onClick={() => handleTemplateSelect(template)}
              className={`p-4 rounded-xl border-2 hover:shadow-lg transition-all text-left bg-white hover:scale-105`}
            >
              <div className={`inline-flex p-2 rounded-lg bg-${template.color}-100 mb-3`}>
                <Icon className={`h-6 w-6 text-${template.color}-600`} />
              </div>
              <h4 className="font-semibold text-gray-900 mb-1">{template.name}</h4>
              <p className="text-xs text-gray-500">Pre-filled template</p>
            </button>
          );
        })}
      </div>

      {/* Clipboard Import */}
      <div className="flex gap-3">
        <button
          onClick={handleClipboardImport}
          className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-700 bg-white hover:bg-gray-50 hover:border-blue-400 transition-all"
        >
          {copiedFromClipboard ? (
            <>
              <Check className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-700">Imported from Clipboard!</span>
            </>
          ) : (
            <>
              <Clipboard className="h-5 w-5" />
              <span className="font-medium">Import from Clipboard</span>
            </>
          )}
        </button>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-900">
          <strong>Tip:</strong> Copy meeting notes from email/Slack/Teams, then click "Import from Clipboard" to auto-populate fields!
        </p>
      </div>
    </div>
  );
}
