"""
AI Project Classifier - Automatically detect meeting subject and assign to projects

This module uses AI to:
1. Analyze meeting transcripts and identify the project/topic
2. Auto-assign meetings to the correct project
3. Organize action items by project
4. Track cross-project dependencies
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from ai_multi_model import orchestrator, ModelType

logger = logging.getLogger(__name__)


@dataclass
class ProjectMatch:
    """A potential project match for a meeting"""
    project_id: str
    project_name: str
    confidence_score: float  # 0.0 - 1.0
    keywords_matched: List[str]
    reasoning: str


@dataclass
class ClassifiedTask:
    """A task/action item classified to a project"""
    task_text: str
    project_id: str
    project_name: str
    confidence: float
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    dependencies: List[str] = None


class ProjectClassifier:
    """
    AI-powered project classification system

    Automatically:
    - Detects meeting subject from transcript
    - Assigns meetings to correct projects
    - Organizes action items by project
    - Tracks cross-project tasks
    """

    def __init__(self):
        # In-memory project database (would be DB in production)
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.project_keywords: Dict[str, List[str]] = {}
        logger.info("🎯 Project Classifier initialized")

    async def register_project(
        self,
        project_id: str,
        project_name: str,
        description: str,
        keywords: Optional[List[str]] = None
    ):
        """
        Register a project for classification

        Args:
            project_id: Unique project identifier
            project_name: Human-readable project name
            description: Project description (used for AI matching)
            keywords: Optional list of keywords (auto-extracted if not provided)
        """

        # If no keywords provided, extract from name and description
        if not keywords:
            keywords = await self._extract_keywords(f"{project_name} {description}")

        self.projects[project_id] = {
            "id": project_id,
            "name": project_name,
            "description": description,
            "created_at": datetime.utcnow()
        }

        self.project_keywords[project_id] = keywords

        logger.info(f"📁 Registered project: {project_name} with {len(keywords)} keywords")

    async def classify_meeting(
        self,
        transcript: str,
        meeting_title: Optional[str] = None,
        participants: Optional[List[str]] = None,
        existing_tags: Optional[List[str]] = None
    ) -> List[ProjectMatch]:
        """
        Classify a meeting to one or more projects using AI

        Args:
            transcript: Full meeting transcript
            meeting_title: Optional meeting title
            participants: Optional list of participants
            existing_tags: Optional tags/labels already assigned

        Returns:
            List of ProjectMatch objects, sorted by confidence (highest first)
        """

        if not self.projects:
            logger.warning("No projects registered for classification")
            return []

        # Build context for AI
        context_parts = []

        if meeting_title:
            context_parts.append(f"Meeting Title: {meeting_title}")

        if participants:
            context_parts.append(f"Participants: {', '.join(participants)}")

        if existing_tags:
            context_parts.append(f"Tags: {', '.join(existing_tags)}")

        context = "\n".join(context_parts)

        # Get first 2000 words of transcript for analysis
        transcript_sample = " ".join(transcript.split()[:2000])

        # Build project list for AI
        project_list = "\n".join([
            f"- {pid}: {proj['name']} - {proj['description']}"
            for pid, proj in self.projects.items()
        ])

        prompt = f"""Analyze this meeting and determine which project(s) it relates to.

{context}

Meeting Transcript Sample:
{transcript_sample}

Available Projects:
{project_list}

For each relevant project, provide:
1. Project ID
2. Confidence score (0.0 to 1.0)
3. Key phrases that match this project
4. Brief reasoning

Format your response as JSON array:
[
  {{
    "project_id": "proj-123",
    "confidence": 0.95,
    "keywords_matched": ["keyword1", "keyword2"],
    "reasoning": "Brief explanation"
  }}
]

Return ONLY the JSON array, no other text."""

        result = await orchestrator.generate(
            prompt,
            model_type=ModelType.CLASSIFICATION,
            prefer_accuracy=True
        )

        # Parse AI response
        matches = await self._parse_project_matches(result["response"])

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"🎯 Found {len(matches)} project matches for meeting")

        return matches

    async def classify_tasks(
        self,
        action_items: List[str],
        meeting_projects: List[ProjectMatch],
        full_transcript: str
    ) -> List[ClassifiedTask]:
        """
        Classify individual action items to specific projects

        Args:
            action_items: List of action items extracted from meeting
            meeting_projects: Projects the meeting was classified to
            full_transcript: Full meeting transcript for context

        Returns:
            List of ClassifiedTask objects
        """

        classified_tasks = []

        for task in action_items:
            # Get primary project (highest confidence from meeting)
            primary_project = meeting_projects[0] if meeting_projects else None

            if not primary_project:
                logger.warning(f"No project match for task: {task[:50]}...")
                continue

            # Check if task mentions specific project
            task_project = await self._detect_task_project(
                task,
                meeting_projects,
                full_transcript
            )

            # Extract assignee and due date from task text
            assignee = self._extract_assignee(task)
            due_date = self._extract_due_date(task)

            classified_task = ClassifiedTask(
                task_text=task,
                project_id=task_project.project_id,
                project_name=task_project.project_name,
                confidence=task_project.confidence_score,
                assignee=assignee,
                due_date=due_date,
                dependencies=[]
            )

            classified_tasks.append(classified_task)

            logger.info(
                f"📋 Classified task to {task_project.project_name} "
                f"(confidence: {task_project.confidence_score:.2f})"
            )

        return classified_tasks

    async def detect_cross_project_dependencies(
        self,
        tasks: List[ClassifiedTask]
    ) -> Dict[str, List[str]]:
        """
        Detect dependencies between tasks across different projects

        Args:
            tasks: List of classified tasks

        Returns:
            Dict mapping task to list of dependent task IDs
        """

        dependencies = {}

        # Build task context for AI
        task_list = "\n".join([
            f"{idx}. [{t.project_name}] {t.task_text}"
            for idx, t in enumerate(tasks)
        ])

        prompt = f"""Analyze these tasks and identify dependencies:

Tasks:
{task_list}

For each task that depends on another task, specify:
- Task number (0-indexed)
- Which other tasks it depends on

Return as JSON:
{{
  "task_index": [list of dependent task indices]
}}

Example:
{{
  "3": [0, 1],
  "5": [2]
}}

Return ONLY the JSON, no other text."""

        result = await orchestrator.generate(
            prompt,
            model_type=ModelType.CLASSIFICATION,
            prefer_accuracy=True
        )

        # Parse and map back to task IDs
        # (Implementation would parse JSON and map indices)

        return dependencies

    async def get_project_summary(
        self,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get summary of all meetings and tasks for a project

        Args:
            project_id: Project to summarize
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with project summary statistics
        """

        if project_id not in self.projects:
            return {"error": "Project not found"}

        project = self.projects[project_id]

        # In production, query database for:
        # - Meetings classified to this project
        # - Tasks assigned to this project
        # - Completion rates
        # - Timeline data

        return {
            "project_id": project_id,
            "project_name": project["name"],
            "total_meetings": 0,  # Query DB
            "total_tasks": 0,     # Query DB
            "completed_tasks": 0, # Query DB
            "active_tasks": 0,    # Query DB
            "participants": [],   # Query DB
            "recent_activity": [] # Query DB
        }

    # === Private Helper Methods ===

    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from project description using AI"""

        prompt = f"""Extract 10-15 key terms/keywords from this project description:

{text}

Return as comma-separated list: keyword1, keyword2, keyword3"""

        result = await orchestrator.generate(
            prompt,
            model_type=ModelType.EXTRACTION,
            prefer_speed=True
        )

        keywords = [k.strip() for k in result["response"].split(",")]
        return keywords[:15]  # Limit to 15

    async def _parse_project_matches(self, ai_response: str) -> List[ProjectMatch]:
        """Parse AI response into ProjectMatch objects"""

        import json

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find array directly
                json_str = re.search(r'\[.*\]', ai_response, re.DOTALL).group(0)

            matches_data = json.loads(json_str)

            matches = []
            for m in matches_data:
                if m["project_id"] in self.projects:
                    project = self.projects[m["project_id"]]
                    matches.append(ProjectMatch(
                        project_id=m["project_id"],
                        project_name=project["name"],
                        confidence_score=float(m.get("confidence", 0.5)),
                        keywords_matched=m.get("keywords_matched", []),
                        reasoning=m.get("reasoning", "")
                    ))

            return matches

        except Exception as e:
            logger.error(f"Failed to parse project matches: {e}")
            # Fallback: keyword matching
            return await self._keyword_fallback_matching(ai_response)

    async def _keyword_fallback_matching(self, transcript: str) -> List[ProjectMatch]:
        """Fallback keyword-based matching if AI parsing fails"""

        matches = []

        for project_id, keywords in self.project_keywords.items():
            matched_keywords = [
                kw for kw in keywords
                if kw.lower() in transcript.lower()
            ]

            if matched_keywords:
                confidence = min(0.8, len(matched_keywords) / len(keywords))

                matches.append(ProjectMatch(
                    project_id=project_id,
                    project_name=self.projects[project_id]["name"],
                    confidence_score=confidence,
                    keywords_matched=matched_keywords,
                    reasoning=f"Keyword match: {len(matched_keywords)} of {len(keywords)}"
                ))

        return matches

    async def _detect_task_project(
        self,
        task: str,
        meeting_projects: List[ProjectMatch],
        transcript: str
    ) -> ProjectMatch:
        """Determine which specific project a task belongs to"""

        # Check if task explicitly mentions project name
        for project in meeting_projects:
            if project.project_name.lower() in task.lower():
                return project

        # Default to primary meeting project (highest confidence)
        return meeting_projects[0]

    def _extract_assignee(self, task: str) -> Optional[str]:
        """Extract assignee from task text"""

        # Look for patterns like:
        # - "John will..."
        # - "Assigned to Mary"
        # - "@username"
        # - "Sarah to..."

        patterns = [
            r'@(\w+)',                              # @username
            r'assigned to (\w+)',                   # assigned to X
            r'(\w+) will',                          # X will
            r'(\w+) to (?:do|complete|finish)',    # X to do
        ]

        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_due_date(self, task: str) -> Optional[datetime]:
        """Extract due date from task text"""

        # Look for date patterns:
        # - "by Friday"
        # - "by end of week"
        # - "by Dec 25"
        # - "due 2025-12-25"

        # Simple implementation - would use dateparser library in production

        date_patterns = [
            (r'by (\w+day)', 7),      # by Friday (assume within week)
            (r'by end of week', 7),
            (r'by end of month', 30),
            (r'next week', 7),
            (r'tomorrow', 1),
        ]

        from datetime import timedelta

        for pattern, days_delta in date_patterns:
            if re.search(pattern, task, re.IGNORECASE):
                return datetime.utcnow() + timedelta(days=days_delta)

        return None


# Singleton instance
classifier = ProjectClassifier()
