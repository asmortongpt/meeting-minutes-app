import React from 'react';
import {
  AlertTriangle, CheckCircle2, Clock, TrendingUp, TrendingDown,
  Users, Calendar, Lightbulb, AlertCircle, MessageSquare, Mail,
  Brain, Sparkles, Target, ArrowRight
} from 'lucide-react';

interface ProactiveInsight {
  smart_suggestions: Array<{
    type: string;
    priority: string;
    title: string;
    auto_draft?: string;
    suggested_date?: string;
    suggested_attendees?: string[];
    confidence: number;
  }>;
  detected_risks: Array<{
    type: string;
    severity: string;
    message: string;
    suggestion?: string;
    tasks?: string[];
    dates?: string[];
  }>;
  follow_up_recommendations: Array<{
    type: string;
    priority: string;
    message: string;
    original_meeting?: string;
    assignee?: string;
    days_overdue?: number;
  }>;
  related_meetings: Array<{
    meeting: any;
    score: number;
    reasons: string[];
  }>;
  pattern_insights: Array<{
    type: string;
    trending_up?: string[];
    trending_down?: string[];
    rate?: number;
    score?: number;
    insight?: string;
    benchmark?: string;
    factors?: any;
  }>;
  proactive_alerts: Array<{
    type: string;
    urgency: string;
    message: string;
    items?: any[];
    suggestion?: string;
  }>;
}

interface SmartInsightsPanelProps {
  insights: ProactiveInsight;
}

const SmartInsightsPanel: React.FC<SmartInsightsPanelProps> = ({ insights }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      default:
        return <Lightbulb className="w-4 h-4 text-blue-600" />;
    }
  };

  return (
    <div className="space-y-6 mt-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-purple-200">
        <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-900">AI Insights & Recommendations</h3>
          <p className="text-sm text-gray-600">Proactive intelligence based on your meeting patterns</p>
        </div>
      </div>

      {/* Proactive Alerts */}
      {insights.proactive_alerts && insights.proactive_alerts.length > 0 && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h4 className="font-semibold text-amber-900">Urgent Alerts</h4>
          </div>
          <div className="space-y-3">
            {insights.proactive_alerts.map((alert, idx) => (
              <div key={idx} className="bg-white/60 rounded-lg p-4 border border-amber-200/50">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-amber-500 rounded-full mt-1.5"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-amber-900">{alert.message}</p>
                    {alert.suggestion && (
                      <p className="text-xs text-amber-700 mt-1">💡 {alert.suggestion}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Smart Suggestions */}
      {insights.smart_suggestions && insights.smart_suggestions.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h4 className="font-semibold text-blue-900">What You'll Need Next</h4>
          </div>
          <div className="space-y-3">
            {insights.smart_suggestions.map((suggestion, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-blue-200/50 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getPriorityIcon(suggestion.priority)}
                    <span className="font-medium text-gray-900">{suggestion.title}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Target className="w-3 h-3" />
                    {Math.round(suggestion.confidence * 100)}% confident
                  </div>
                </div>

                {suggestion.auto_draft && (
                  <div className="mt-3 p-3 bg-gray-50 rounded border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Mail className="w-4 h-4 text-gray-600" />
                      <span className="text-xs font-medium text-gray-700">Auto-generated draft:</span>
                    </div>
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono">
                      {suggestion.auto_draft}
                    </pre>
                  </div>
                )}

                {suggestion.suggested_attendees && (
                  <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                    <Users className="w-4 h-4" />
                    <span>Suggested attendees: {suggestion.suggested_attendees.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detected Risks */}
      {insights.detected_risks && insights.detected_risks.length > 0 && (
        <div className="bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <h4 className="font-semibold text-red-900">Potential Risks Detected</h4>
          </div>
          <div className="space-y-3">
            {insights.detected_risks.map((risk, idx) => (
              <div key={idx} className={`rounded-lg p-4 border ${getSeverityColor(risk.severity)}`}>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{risk.message}</p>
                    {risk.suggestion && (
                      <p className="text-xs mt-2 flex items-center gap-2">
                        <Lightbulb className="w-3 h-3" />
                        {risk.suggestion}
                      </p>
                    )}
                    {risk.tasks && risk.tasks.length > 0 && (
                      <div className="mt-2 text-xs space-y-1">
                        {risk.tasks.map((task, tidx) => (
                          <div key={tidx} className="flex items-center gap-2">
                            <ArrowRight className="w-3 h-3" />
                            <span>{task}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Follow-up Recommendations */}
      {insights.follow_up_recommendations && insights.follow_up_recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-purple-600" />
            <h4 className="font-semibold text-purple-900">Action Item Follow-ups</h4>
          </div>
          <div className="space-y-3">
            {insights.follow_up_recommendations.map((followup, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-purple-200/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {followup.type === 'overdue_action' ? (
                      <Clock className="w-4 h-4 text-red-600 mt-0.5" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{followup.message}</p>
                      {followup.original_meeting && (
                        <p className="text-xs text-gray-600 mt-1">
                          From: {followup.original_meeting}
                        </p>
                      )}
                      {followup.assignee && (
                        <p className="text-xs text-gray-600 mt-1">
                          Assigned to: {followup.assignee}
                        </p>
                      )}
                    </div>
                  </div>
                  {followup.days_overdue && followup.days_overdue > 0 && (
                    <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                      {followup.days_overdue}d overdue
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pattern Insights */}
      {insights.pattern_insights && insights.pattern_insights.length > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-600" />
            <h4 className="font-semibold text-green-900">Pattern Analysis</h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.pattern_insights.map((pattern, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-green-200/50">
                {pattern.type === 'topic_trends' && (
                  <>
                    <h5 className="text-sm font-semibold text-gray-900 mb-3">Topic Trends</h5>
                    {pattern.trending_up && pattern.trending_up.length > 0 && (
                      <div className="mb-2">
                        <div className="flex items-center gap-2 text-xs text-green-700 mb-1">
                          <TrendingUp className="w-3 h-3" />
                          <span className="font-medium">Trending Up:</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {pattern.trending_up.map((topic, tidx) => (
                            <span key={tidx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {pattern.trending_down && pattern.trending_down.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 text-xs text-gray-600 mb-1">
                          <TrendingDown className="w-3 h-3" />
                          <span className="font-medium">Trending Down:</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {pattern.trending_down.map((topic, tidx) => (
                            <span key={tidx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                              {topic}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {pattern.type === 'completion_rate' && (
                  <>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2">Task Completion</h5>
                    <div className="flex items-center gap-3">
                      <div className="text-3xl font-bold text-green-600">{pattern.rate}%</div>
                      <div className="flex-1">
                        <p className="text-xs text-gray-600">{pattern.insight}</p>
                        {pattern.benchmark && (
                          <p className="text-xs text-gray-500 mt-1">{pattern.benchmark}</p>
                        )}
                      </div>
                    </div>
                  </>
                )}

                {pattern.type === 'effectiveness' && (
                  <>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2">Meeting Effectiveness</h5>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="text-3xl font-bold text-green-600">{pattern.score}/10</div>
                    </div>
                    {pattern.factors && (
                      <div className="space-y-1 text-xs text-gray-600">
                        <div>📋 Avg action items: {pattern.factors.action_items_per_meeting}</div>
                        <div>✅ Avg decisions: {pattern.factors.decisions_per_meeting}</div>
                        <div>🎯 Follow-through: {pattern.factors.follow_through_rate}%</div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Meetings */}
      {insights.related_meetings && insights.related_meetings.length > 0 && (
        <div className="bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="w-5 h-5 text-gray-600" />
            <h4 className="font-semibold text-gray-900">Related Meetings</h4>
          </div>
          <div className="space-y-3">
            {insights.related_meetings.slice(0, 3).map((related, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200/50 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <h5 className="font-medium text-gray-900">{related.meeting.title || 'Untitled Meeting'}</h5>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Target className="w-3 h-3" />
                    {related.score}% match
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {related.reasons.map((reason, ridx) => (
                    <span key={ridx} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      {reason}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartInsightsPanel;
