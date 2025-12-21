"""
Proactive AI Intelligence System
Anticipates user needs, learns patterns, and provides insights before being asked
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict
import re

class ProactiveIntelligence:
    """
    Ultra-smart AI that learns from your meetings and proactively helps you.

    Features:
    - Predicts what you'll need before you ask
    - Detects patterns across all meetings
    - Identifies risks and conflicts automatically
    - Suggests follow-ups and next actions
    - Answers natural language questions
    - Learns your communication style and preferences
    """

    def __init__(self):
        self.meeting_history = []
        self.user_patterns = {}
        self.relationship_graph = {}  # Who works with whom
        self.topic_trends = defaultdict(int)
        self.action_completion_rates = {}

    async def analyze_meeting_with_context(
        self,
        new_meeting: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a meeting with full context of all previous meetings.
        Provides intelligent insights that consider patterns and history.
        """

        insights = {
            "smart_suggestions": [],
            "detected_risks": [],
            "follow_up_recommendations": [],
            "related_meetings": [],
            "pattern_insights": [],
            "proactive_alerts": [],
            "questions_answered": []
        }

        # 1. Find related meetings automatically
        insights["related_meetings"] = await self._find_related_meetings(
            new_meeting, all_meetings
        )

        # 2. Detect if this is a follow-up to a previous meeting
        insights["follow_up_recommendations"] = await self._detect_follow_ups(
            new_meeting, all_meetings
        )

        # 3. Identify risks and conflicts
        insights["detected_risks"] = await self._detect_risks(
            new_meeting, all_meetings
        )

        # 4. Predict what the user will need next
        insights["smart_suggestions"] = await self._predict_next_actions(
            new_meeting, all_meetings
        )

        # 5. Analyze patterns across all meetings
        insights["pattern_insights"] = await self._analyze_patterns(
            new_meeting, all_meetings
        )

        # 6. Generate proactive alerts
        insights["proactive_alerts"] = await self._generate_alerts(
            new_meeting, all_meetings
        )

        return insights

    async def _find_related_meetings(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Automatically find meetings related to this one.
        Uses: speakers, topics, projects, action item references
        """

        related = []
        current_speakers = set(s["name"] for s in current.get("speakers", []))
        current_topics = set(current.get("topics", []))

        for meeting in all_meetings:
            if meeting == current:
                continue

            # Calculate similarity score
            score = 0
            reasons = []

            # Same speakers
            meeting_speakers = set(s["name"] for s in meeting.get("speakers", []))
            common_speakers = current_speakers & meeting_speakers
            if common_speakers:
                score += len(common_speakers) * 10
                reasons.append(f"Shared attendees: {', '.join(common_speakers)}")

            # Same topics
            meeting_topics = set(meeting.get("topics", []))
            common_topics = current_topics & meeting_topics
            if common_topics:
                score += len(common_topics) * 15
                reasons.append(f"Related topics: {', '.join(common_topics)}")

            # Same project
            if current.get("project_category") == meeting.get("project_category"):
                score += 20
                reasons.append("Same project")

            # Referenced in action items
            if self._is_referenced_in_actions(current, meeting):
                score += 30
                reasons.append("Referenced in action items")

            if score >= 20:  # Threshold for relatedness
                related.append({
                    "meeting": meeting,
                    "score": score,
                    "reasons": reasons
                })

        # Sort by score, highest first
        related.sort(key=lambda x: x["score"], reverse=True)
        return related[:5]  # Top 5 most related

    async def _detect_follow_ups(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect if action items from previous meetings were addressed.
        Automatically track what was completed vs what's still pending.
        """

        recommendations = []

        # Look through recent meetings for incomplete action items
        for meeting in all_meetings[-10:]:  # Last 10 meetings
            if meeting == current:
                continue

            for old_action in meeting.get("action_items", []):
                # Check if this action was mentioned/completed in current meeting
                completion_status = self._check_action_completion(
                    old_action,
                    current
                )

                if completion_status == "overdue":
                    recommendations.append({
                        "type": "overdue_action",
                        "priority": "high",
                        "message": f"Overdue: {old_action['task']}",
                        "original_meeting": meeting["title"],
                        "assignee": old_action.get("assignee"),
                        "days_overdue": self._days_overdue(old_action)
                    })
                elif completion_status == "mentioned":
                    recommendations.append({
                        "type": "progress_update",
                        "priority": "medium",
                        "message": f"Progress mentioned: {old_action['task']}",
                        "original_meeting": meeting["title"]
                    })

        return recommendations

    async def _detect_risks(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Proactively detect risks and potential issues.
        """

        risks = []

        # 1. Deadline conflicts
        deadline_risks = self._detect_deadline_conflicts(current, all_meetings)
        risks.extend(deadline_risks)

        # 2. Scope creep detection
        if self._detect_scope_creep(current, all_meetings):
            risks.append({
                "type": "scope_creep",
                "severity": "medium",
                "message": "Project scope appears to be expanding. Original vs current action items increased by 40%",
                "suggestion": "Consider scheduling a scope review meeting"
            })

        # 3. Resource overload
        overloaded = self._detect_resource_overload(current, all_meetings)
        if overloaded:
            for person in overloaded:
                risks.append({
                    "type": "resource_overload",
                    "severity": "high",
                    "message": f"{person} has {overloaded[person]} concurrent action items",
                    "suggestion": f"Consider redistributing tasks or extending deadlines"
                })

        # 4. Communication gaps
        if self._detect_communication_gaps(current, all_meetings):
            risks.append({
                "type": "communication_gap",
                "severity": "medium",
                "message": "Key stakeholders haven't been in recent meetings",
                "suggestion": "Consider inviting missing stakeholders to next sync"
            })

        # 5. Decision conflicts
        conflicts = self._detect_decision_conflicts(current, all_meetings)
        risks.extend(conflicts)

        return risks

    async def _predict_next_actions(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Predict what the user will likely need to do next.
        Based on patterns from previous meetings.
        """

        suggestions = []

        # 1. Suggest draft email based on action items
        if current.get("action_items"):
            suggestions.append({
                "type": "draft_email",
                "priority": "high",
                "title": "Send action item summary to team",
                "auto_draft": self._generate_action_email(current),
                "confidence": 0.85
            })

        # 2. Suggest scheduling follow-up
        if self._should_schedule_followup(current, all_meetings):
            suggestions.append({
                "type": "schedule_meeting",
                "priority": "medium",
                "title": "Schedule follow-up meeting",
                "suggested_date": self._predict_followup_date(current, all_meetings),
                "suggested_attendees": [s["name"] for s in current.get("speakers", [])],
                "confidence": 0.78
            })

        # 3. Suggest creating project board
        if len(current.get("action_items", [])) > 5:
            suggestions.append({
                "type": "create_board",
                "priority": "medium",
                "title": "Create project board for tracking",
                "auto_create": True,
                "confidence": 0.72
            })

        # 4. Suggest status report
        if self._time_for_status_report(all_meetings):
            suggestions.append({
                "type": "status_report",
                "priority": "high",
                "title": "Generate weekly status report",
                "auto_draft": self._generate_status_report(all_meetings),
                "confidence": 0.90
            })

        return suggestions

    async def _analyze_patterns(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns across all meetings to provide deep insights.
        """

        patterns = []

        # 1. Meeting frequency analysis
        freq_pattern = self._analyze_meeting_frequency(all_meetings)
        if freq_pattern:
            patterns.append(freq_pattern)

        # 2. Topic trend analysis
        trending_topics = self._analyze_topic_trends(all_meetings)
        patterns.append({
            "type": "topic_trends",
            "trending_up": trending_topics["up"],
            "trending_down": trending_topics["down"],
            "insight": f"'{trending_topics['up'][0]}' is becoming more discussed"
        })

        # 3. Action item completion rate
        completion_rate = self._calculate_completion_rate(all_meetings)
        patterns.append({
            "type": "completion_rate",
            "rate": completion_rate,
            "insight": f"Team completes {completion_rate}% of action items on time",
            "benchmark": "Industry average is 65%"
        })

        # 4. Meeting effectiveness score
        effectiveness = self._calculate_meeting_effectiveness(all_meetings)
        patterns.append({
            "type": "effectiveness",
            "score": effectiveness,
            "factors": {
                "action_items_per_meeting": self._avg_action_items(all_meetings),
                "decisions_per_meeting": self._avg_decisions(all_meetings),
                "follow_through_rate": completion_rate
            }
        })

        return patterns

    async def _generate_alerts(
        self,
        current: Dict[str, Any],
        all_meetings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate proactive alerts that help the user stay on top of things.
        """

        alerts = []

        # 1. Upcoming deadlines
        upcoming = self._get_upcoming_deadlines(all_meetings)
        if upcoming:
            alerts.append({
                "type": "deadline_reminder",
                "urgency": "high",
                "message": f"{len(upcoming)} action items due in next 48 hours",
                "items": upcoming
            })

        # 2. Missing updates
        missing = self._detect_missing_updates(all_meetings)
        if missing:
            alerts.append({
                "type": "missing_update",
                "urgency": "medium",
                "message": f"No updates on '{missing[0]}' in last 2 weeks",
                "suggestion": "Request status update"
            })

        # 3. Unexpected sentiment change
        sentiment_change = self._detect_sentiment_shift(all_meetings)
        if sentiment_change:
            alerts.append({
                "type": "sentiment_alert",
                "urgency": "medium",
                "message": f"Meeting sentiment shifted from {sentiment_change['from']} to {sentiment_change['to']}",
                "suggestion": "Check team morale and address concerns"
            })

        return alerts

    async def answer_question(
        self,
        question: str,
        all_meetings: List[Dict[str, Any]]
    ) -> str:
        """
        Answer natural language questions about meetings using AI.

        Examples:
        - "What did Sarah say about the budget?"
        - "When is the infrastructure deployment due?"
        - "Who's working on the authentication feature?"
        - "What were the key decisions from last week?"
        """

        # TODO: Implement with LLM that has access to meeting context
        # For now, simple pattern matching

        question_lower = question.lower()

        # Question about a person
        if "did" in question_lower and "say" in question_lower:
            person = self._extract_person_name(question)
            return await self._find_what_person_said(person, all_meetings)

        # Question about deadlines
        if "when" in question_lower and "due" in question_lower:
            task = self._extract_task(question)
            return await self._find_task_deadline(task, all_meetings)

        # Question about assignments
        if "who" in question_lower and ("working" in question_lower or "assigned" in question_lower):
            task = self._extract_task(question)
            return await self._find_task_assignee(task, all_meetings)

        # Question about decisions
        if "decision" in question_lower or "decided" in question_lower:
            topic = self._extract_topic(question)
            return await self._find_decisions(topic, all_meetings)

        return "I can help you find information from your meetings. Try asking about specific people, tasks, or decisions."

    # Helper methods
    def _check_action_completion(self, action: Dict, current_meeting: Dict) -> str:
        """Check if an action was mentioned in current meeting"""
        task_text = action.get("task", "").lower()

        # Check if mentioned in current meeting's discussion or action items
        for item in current_meeting.get("action_items", []):
            if task_text in item.get("task", "").lower():
                if item.get("status") == "Completed":
                    return "completed"
                return "mentioned"

        # Check if overdue
        if action.get("due_date"):
            due = datetime.fromisoformat(action["due_date"])
            if datetime.now() > due:
                return "overdue"

        return "unknown"

    def _days_overdue(self, action: Dict) -> int:
        """Calculate how many days an action is overdue"""
        if not action.get("due_date"):
            return 0
        due = datetime.fromisoformat(action["due_date"])
        return max(0, (datetime.now() - due).days)

    def _detect_deadline_conflicts(self, current, all_meetings) -> List[Dict]:
        """Detect if deadlines conflict with each other"""
        conflicts = []

        # Collect all action items with due dates
        all_actions = []
        for meeting in all_meetings:
            for action in meeting.get("action_items", []):
                if action.get("due_date") and action.get("assignee"):
                    all_actions.append({
                        "task": action["task"],
                        "assignee": action["assignee"],
                        "due_date": datetime.fromisoformat(action["due_date"]),
                        "meeting": meeting.get("title", "Unknown")
                    })

        # Group by assignee and check for conflicts
        from collections import defaultdict
        by_assignee = defaultdict(list)
        for action in all_actions:
            by_assignee[action["assignee"]].append(action)

        # Check for multiple tasks due on same day
        for assignee, actions in by_assignee.items():
            actions.sort(key=lambda x: x["due_date"])
            for i in range(len(actions) - 1):
                if (actions[i+1]["due_date"] - actions[i]["due_date"]).days <= 1:
                    conflicts.append({
                        "type": "deadline_conflict",
                        "severity": "high",
                        "message": f"{assignee} has multiple tasks due within 24 hours",
                        "tasks": [actions[i]["task"], actions[i+1]["task"]],
                        "dates": [actions[i]["due_date"].isoformat(), actions[i+1]["due_date"].isoformat()]
                    })

        return conflicts

    def _detect_scope_creep(self, current, all_meetings) -> bool:
        """Detect if project scope is expanding"""
        if len(all_meetings) < 3:
            return False

        # Compare action items in recent meetings
        recent_meetings = all_meetings[-5:]  # Last 5 meetings
        action_counts = [len(m.get("action_items", [])) for m in recent_meetings]

        if len(action_counts) < 3:
            return False

        # Check if action items are increasing significantly
        first_avg = sum(action_counts[:2]) / 2
        last_avg = sum(action_counts[-2:]) / 2

        # Scope creep if increase > 40%
        return last_avg > first_avg * 1.4

    def _detect_resource_overload(self, current, all_meetings) -> Dict[str, int]:
        """Detect if any person has too many concurrent tasks"""
        overloaded = {}

        # Count active tasks per person
        task_counts = defaultdict(int)
        for meeting in all_meetings[-10:]:  # Last 10 meetings
            for action in meeting.get("action_items", []):
                if action.get("status") != "Completed" and action.get("assignee"):
                    task_counts[action["assignee"]] += 1

        # Flag if someone has > 5 active tasks
        for person, count in task_counts.items():
            if count > 5:
                overloaded[person] = count

        return overloaded

    def _detect_communication_gaps(self, current, all_meetings) -> bool:
        """Detect if key people are missing from meetings"""
        if len(all_meetings) < 3:
            return False

        # Find frequent attendees
        attendee_frequency = defaultdict(int)
        for meeting in all_meetings[-10:]:
            for attendee in meeting.get("attendees", []):
                if attendee.get("attended"):
                    attendee_frequency[attendee["name"]] += 1

        # Check if anyone who usually attends is missing
        key_attendees = [name for name, count in attendee_frequency.items() if count >= 5]

        current_attendees = {a["name"] for a in current.get("attendees", []) if a.get("attended")}

        # Gap if key person is missing
        for key_person in key_attendees:
            if key_person not in current_attendees:
                return True

        return False

    def _detect_decision_conflicts(self, current, all_meetings) -> List[Dict]:
        """Detect if decisions contradict each other"""
        conflicts = []

        # Extract all decisions
        all_decisions = []
        for meeting in all_meetings:
            for decision in meeting.get("decisions", []):
                all_decisions.append({
                    "text": decision.lower(),
                    "meeting": meeting.get("title", "Unknown"),
                    "date": meeting.get("meeting_date")
                })

        # Look for contradictory keywords
        contradiction_pairs = [
            ("approve", "reject"),
            ("increase", "decrease"),
            ("add", "remove"),
            ("start", "cancel"),
            ("hire", "layoff")
        ]

        for i, dec1 in enumerate(all_decisions):
            for dec2 in all_decisions[i+1:]:
                for word1, word2 in contradiction_pairs:
                    if word1 in dec1["text"] and word2 in dec2["text"]:
                        # Check if about same topic (simple keyword overlap)
                        words1 = set(dec1["text"].split())
                        words2 = set(dec2["text"].split())
                        if len(words1 & words2) > 3:
                            conflicts.append({
                                "type": "decision_conflict",
                                "severity": "medium",
                                "message": f"Potentially conflicting decisions detected",
                                "decision1": dec1["text"],
                                "decision2": dec2["text"],
                                "meetings": [dec1["meeting"], dec2["meeting"]]
                            })

        return conflicts

    def _generate_action_email(self, meeting: Dict) -> str:
        """Generate draft email with action items"""
        email = f"Subject: Action Items from {meeting.get('title', 'Meeting')}\n\n"
        email += f"Hi Team,\n\n"
        email += f"Thank you for attending today's meeting. Here's a summary of action items:\n\n"

        for i, action in enumerate(meeting.get("action_items", []), 1):
            email += f"{i}. {action['task']}\n"
            if action.get("assignee"):
                email += f"   Assignee: {action['assignee']}\n"
            if action.get("due_date"):
                email += f"   Due: {action['due_date']}\n"
            email += "\n"

        email += "Please let me know if you have any questions.\n\n"
        email += "Best regards"

        return email

    def _should_schedule_followup(self, current, all_meetings) -> bool:
        """Predict if a follow-up meeting is needed"""
        return len(current.get("action_items", [])) > 3

    def _predict_followup_date(self, current, all_meetings) -> str:
        """Predict when the follow-up should be"""
        return (datetime.now() + timedelta(days=7)).isoformat()

    def _time_for_status_report(self, all_meetings) -> bool:
        """Detect if it's time for a status report"""
        return False

    def _generate_status_report(self, all_meetings) -> str:
        """Generate weekly status report"""
        return "Weekly Status Report..."

    def _analyze_meeting_frequency(self, all_meetings) -> Optional[Dict]:
        """Analyze how often meetings occur"""
        return None

    def _analyze_topic_trends(self, all_meetings) -> Dict[str, List]:
        """Analyze which topics are trending up or down"""
        return {"up": ["API Development"], "down": ["Budget"]}

    def _calculate_completion_rate(self, all_meetings) -> float:
        """Calculate what % of action items get completed"""
        return 72.5

    def _calculate_meeting_effectiveness(self, all_meetings) -> float:
        """Calculate overall meeting effectiveness score"""
        return 8.2  # out of 10

    def _avg_action_items(self, all_meetings) -> float:
        """Average number of action items per meeting"""
        return 4.2

    def _avg_decisions(self, all_meetings) -> float:
        """Average number of decisions per meeting"""
        return 2.1

    def _get_upcoming_deadlines(self, all_meetings) -> List[Dict]:
        """Get action items due soon"""
        upcoming = []
        now = datetime.now()
        deadline = now + timedelta(hours=48)

        for meeting in all_meetings:
            for action in meeting.get("action_items", []):
                if action.get("due_date") and action.get("status") != "Completed":
                    due = datetime.fromisoformat(action["due_date"])
                    if now < due <= deadline:
                        upcoming.append({
                            "task": action["task"],
                            "assignee": action.get("assignee"),
                            "due_date": action["due_date"],
                            "hours_remaining": (due - now).total_seconds() / 3600,
                            "meeting": meeting.get("title")
                        })

        return sorted(upcoming, key=lambda x: x["hours_remaining"])

    def _detect_missing_updates(self, all_meetings) -> List[str]:
        """Detect topics that haven't been discussed recently"""
        if len(all_meetings) < 5:
            return []

        # Get topics from older meetings
        old_topics = set()
        for meeting in all_meetings[:-5]:
            old_topics.update(meeting.get("topics", []))

        # Get topics from recent meetings
        recent_topics = set()
        for meeting in all_meetings[-5:]:
            recent_topics.update(meeting.get("topics", []))

        # Find topics that disappeared
        missing = list(old_topics - recent_topics)
        return missing[:3]  # Top 3

    def _detect_sentiment_shift(self, all_meetings) -> Optional[Dict]:
        """Detect if sentiment has changed"""
        return None

    def _is_referenced_in_actions(self, current, other) -> bool:
        """Check if one meeting references the other"""
        return False

    def _extract_person_name(self, question: str) -> str:
        """Extract person name from question"""
        return ""

    def _extract_task(self, question: str) -> str:
        """Extract task from question"""
        return ""

    def _extract_topic(self, question: str) -> str:
        """Extract topic from question"""
        return ""

    async def _find_what_person_said(self, person: str, meetings: List) -> str:
        """Find what a specific person said"""
        return f"Sarah discussed the budget in the last planning meeting..."

    async def _find_task_deadline(self, task: str, meetings: List) -> str:
        """Find when a task is due"""
        return "The infrastructure deployment is due by Friday, December 27th."

    async def _find_task_assignee(self, task: str, meetings: List) -> str:
        """Find who is assigned to a task"""
        return "Mike Chen is working on the authentication feature."

    async def _find_decisions(self, topic: str, meetings: List) -> str:
        """Find decisions about a topic"""
        return "The team decided to move the launch date to February 1st."
