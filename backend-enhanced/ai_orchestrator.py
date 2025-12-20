"""
Multi-Model AI Orchestration System
Intelligently routes tasks to best AI model with fallback and parallel processing
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import anthropic
import openai
from google import generativeai as genai
import tiktoken
from dataclasses import dataclass
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)


class AIModel(str, Enum):
    """Available AI models"""
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4_VISION = "gpt-4-vision-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"


class TaskType(str, Enum):
    """AI task categories"""
    TRANSCRIPTION = "transcription"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ACTION_EXTRACTION = "action_extraction"
    SUMMARY_GENERATION = "summary_generation"
    SPEAKER_DIARIZATION = "speaker_diarization"
    SCREENSHOT_ANALYSIS = "screenshot_analysis"
    DECISION_EXTRACTION = "decision_extraction"
    TOPIC_CLASSIFICATION = "topic_classification"
    DEADLINE_PREDICTION = "deadline_prediction"
    MEETING_SCORING = "meeting_scoring"


@dataclass
class AIResponse:
    """Standardized AI response"""
    success: bool
    model: str
    task_type: str
    result: Any
    confidence: float
    processing_time: float
    tokens_used: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class AIOrchestrator:
    """
    Intelligent AI orchestration with:
    - Multi-model support (Claude, GPT-4, Gemini)
    - Automatic model selection based on task
    - Parallel processing for speed
    - Fallback on failure
    - Cost optimization
    - Quality scoring
    """

    def __init__(self):
        # Initialize clients
        self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Token counter
        self.token_encoder = tiktoken.get_encoding("cl100k_base")

        # Model routing rules
        self.model_routing = {
            TaskType.TRANSCRIPTION: [AIModel.GPT4_TURBO],  # Whisper API
            TaskType.SENTIMENT_ANALYSIS: [AIModel.CLAUDE_SONNET, AIModel.GPT4_TURBO, AIModel.GEMINI_PRO],
            TaskType.ACTION_EXTRACTION: [AIModel.CLAUDE_SONNET, AIModel.GPT4_TURBO],
            TaskType.SUMMARY_GENERATION: [AIModel.CLAUDE_SONNET, AIModel.GPT4_TURBO, AIModel.GEMINI_FLASH],
            TaskType.SPEAKER_DIARIZATION: [AIModel.GPT4_TURBO, AIModel.CLAUDE_SONNET],
            TaskType.SCREENSHOT_ANALYSIS: [AIModel.GPT4_VISION, AIModel.CLAUDE_SONNET],
            TaskType.DECISION_EXTRACTION: [AIModel.CLAUDE_SONNET, AIModel.GPT4_TURBO],
            TaskType.TOPIC_CLASSIFICATION: [AIModel.GEMINI_FLASH, AIModel.GPT35_TURBO, AIModel.CLAUDE_HAIKU],
            TaskType.DEADLINE_PREDICTION: [AIModel.GPT4_TURBO, AIModel.CLAUDE_SONNET],
            TaskType.MEETING_SCORING: [AIModel.CLAUDE_SONNET, AIModel.GPT4_TURBO],
        }

    async def process_task(
        self,
        task_type: TaskType,
        content: str,
        context: Optional[Dict] = None,
        use_parallel: bool = False
    ) -> AIResponse:
        """
        Process a task with optimal AI model

        Args:
            task_type: Type of AI task
            content: Input content
            context: Additional context
            use_parallel: Use multiple models in parallel for consensus
        """
        start_time = datetime.utcnow()
        models = self.model_routing.get(task_type, [AIModel.CLAUDE_SONNET])

        try:
            if use_parallel and len(models) > 1:
                # Run multiple models in parallel for higher quality
                responses = await asyncio.gather(
                    *[self._call_model(model, task_type, content, context) for model in models[:2]],
                    return_exceptions=True
                )
                # Use consensus or best response
                valid_responses = [r for r in responses if isinstance(r, AIResponse) and r.success]
                if valid_responses:
                    return max(valid_responses, key=lambda x: x.confidence)
                else:
                    return await self._call_model(models[0], task_type, content, context)
            else:
                # Use primary model with fallback
                for model in models:
                    try:
                        response = await self._call_model(model, task_type, content, context)
                        if response.success:
                            return response
                    except Exception as e:
                        logger.warning(f"Model {model} failed, trying fallback: {str(e)}")
                        continue

                # All models failed
                return AIResponse(
                    success=False,
                    model=models[0],
                    task_type=task_type.value,
                    result=None,
                    confidence=0.0,
                    processing_time=(datetime.utcnow() - start_time).total_seconds(),
                    tokens_used=0,
                    error="All models failed"
                )

        except Exception as e:
            logger.error(f"AI orchestration error: {str(e)}")
            return AIResponse(
                success=False,
                model="unknown",
                task_type=task_type.value,
                result=None,
                confidence=0.0,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                tokens_used=0,
                error=str(e)
            )

    async def _call_model(
        self,
        model: AIModel,
        task_type: TaskType,
        content: str,
        context: Optional[Dict] = None
    ) -> AIResponse:
        """Call specific AI model"""
        start_time = datetime.utcnow()

        # Get task-specific prompt
        prompt = self._get_prompt(task_type, content, context)

        # Count tokens
        tokens_used = len(self.token_encoder.encode(prompt))

        try:
            if model in [AIModel.CLAUDE_OPUS, AIModel.CLAUDE_SONNET, AIModel.CLAUDE_HAIKU]:
                result = await self._call_claude(model, prompt, task_type)
            elif model in [AIModel.GPT4_TURBO, AIModel.GPT4_VISION, AIModel.GPT35_TURBO]:
                result = await self._call_gpt(model, prompt, task_type)
            elif model in [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH]:
                result = await self._call_gemini(model, prompt, task_type)
            else:
                raise ValueError(f"Unknown model: {model}")

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return AIResponse(
                success=True,
                model=model.value,
                task_type=task_type.value,
                result=result,
                confidence=self._calculate_confidence(result, task_type),
                processing_time=processing_time,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Model {model} error: {str(e)}")
            raise

    async def _call_claude(self, model: AIModel, prompt: str, task_type: TaskType) -> Dict:
        """Call Claude API"""
        message = self.anthropic_client.messages.create(
            model=model.value,
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        return self._parse_response(response_text, task_type)

    async def _call_gpt(self, model: AIModel, prompt: str, task_type: TaskType) -> Dict:
        """Call OpenAI GPT API"""
        response = await self.openai_client.chat.completions.create(
            model=model.value,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE
        )

        response_text = response.choices[0].message.content
        return self._parse_response(response_text, task_type)

    async def _call_gemini(self, model: AIModel, prompt: str, task_type: TaskType) -> Dict:
        """Call Google Gemini API"""
        gemini_model = genai.GenerativeModel(model.value)
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)

        response_text = response.text
        return self._parse_response(response_text, task_type)

    def _get_prompt(self, task_type: TaskType, content: str, context: Optional[Dict] = None) -> str:
        """Generate task-specific prompts"""
        prompts = {
            TaskType.SENTIMENT_ANALYSIS: f"""Analyze the sentiment of this meeting content.

Content: {content}

Provide a comprehensive sentiment analysis with:
1. Overall meeting sentiment (positive/neutral/negative with score 0-100)
2. Sentiment by speaker (if identifiable)
3. Sentiment by topic discussed
4. Emotional tone indicators
5. Engagement level (0-100)

Return as JSON:
{{
    "overall_sentiment": {{
        "label": "positive|neutral|negative",
        "score": 85,
        "confidence": 0.92
    }},
    "by_speaker": [
        {{"speaker": "name", "sentiment": "positive", "score": 90}}
    ],
    "by_topic": [
        {{"topic": "Budget", "sentiment": "negative", "score": 30}}
    ],
    "engagement_level": 78,
    "emotional_indicators": ["enthusiasm", "concern", "optimism"]
}}""",

            TaskType.ACTION_EXTRACTION: f"""Extract all action items from this meeting.

Content: {content}

Identify ALL action items with:
1. Clear description of the task
2. Owner/assignee (who is responsible)
3. Due date (if mentioned, else predict reasonable deadline)
4. Priority (low/medium/high/critical)
5. Dependencies (if any)
6. Confidence score (0.0-1.0)

Return as JSON:
{{
    "action_items": [
        {{
            "description": "Complete budget analysis for Q2",
            "owner": "John Smith",
            "due_date": "2024-02-15",
            "priority": "high",
            "dependencies": ["Budget approval"],
            "confidence": 0.95,
            "context": "Mentioned during budget discussion"
        }}
    ]
}}""",

            TaskType.SUMMARY_GENERATION: f"""Generate a comprehensive meeting summary.

Content: {content}

Create a professional summary with:
1. Executive summary (2-3 sentences)
2. Key discussion points
3. Major decisions made
4. Action items identified
5. Next steps
6. Risks and concerns raised

Return as JSON:
{{
    "executive_summary": "Brief overview...",
    "key_points": ["Point 1", "Point 2"],
    "decisions": ["Decision 1", "Decision 2"],
    "action_items_summary": "Brief action items overview",
    "next_steps": ["Step 1", "Step 2"],
    "risks": ["Risk 1", "Risk 2"],
    "overall_tone": "positive"
}}""",

            TaskType.DECISION_EXTRACTION: f"""Extract all key decisions made in this meeting.

Content: {content}

Identify ALL decisions with:
1. Clear statement of the decision
2. Who made the decision
3. Rationale/context
4. Impact assessment
5. Confidence level

Return as JSON:
{{
    "decisions": [
        {{
            "decision": "Approved budget increase by 15%",
            "decided_by": "Executive team",
            "rationale": "Market expansion requires additional investment",
            "impact": "high",
            "confidence": 0.98
        }}
    ]
}}""",

            TaskType.SPEAKER_DIARIZATION: f"""Identify and label all speakers in this transcript.

Content: {content}

For each speaker:
1. Unique identifier
2. Speaking time
3. Number of utterances
4. Key topics discussed
5. Sentiment

Return as JSON:
{{
    "speakers": [
        {{
            "id": "Speaker_1",
            "name": "Identified Name or Unknown",
            "speaking_time_seconds": 180,
            "utterance_count": 12,
            "topics": ["Budget", "Timeline"],
            "sentiment": "positive"
        }}
    ],
    "total_speakers": 4
}}""",

            TaskType.TOPIC_CLASSIFICATION: f"""Classify the main topics discussed in this meeting.

Content: {content}

Identify:
1. Primary topics
2. Time spent on each
3. Importance level
4. Related subtopics

Return as JSON:
{{
    "topics": [
        {{
            "name": "Budget Planning",
            "importance": "high",
            "time_percentage": 35,
            "subtopics": ["Q2 forecast", "Cost reduction"]
        }}
    ],
    "primary_topic": "Budget Planning",
    "meeting_category": "planning"
}}""",

            TaskType.DEADLINE_PREDICTION: f"""Predict realistic deadlines for action items.

Context: {context}
Action items: {content}

For each item, predict:
1. Suggested deadline
2. Confidence in prediction
3. Rationale
4. Risk factors

Return as JSON:
{{
    "predictions": [
        {{
            "action_item": "Complete analysis",
            "suggested_deadline": "2024-02-20",
            "confidence": 0.85,
            "rationale": "Based on complexity and standard timelines",
            "risk_factors": ["Dependency on external data"]
        }}
    ]
}}""",

            TaskType.MEETING_SCORING: f"""Score this meeting's effectiveness.

Content: {content}

Evaluate on:
1. Productivity (0-100)
2. Clarity of outcomes (0-100)
3. Time efficiency (0-100)
4. Participant engagement (0-100)
5. Action item quality (0-100)

Return as JSON:
{{
    "overall_score": 85,
    "productivity": 90,
    "clarity": 85,
    "time_efficiency": 80,
    "engagement": 88,
    "action_item_quality": 87,
    "strengths": ["Clear decisions", "Good participation"],
    "improvements": ["Could be more concise"],
    "grade": "A"
}}""",
        }

        return prompts.get(task_type, f"Analyze this content:\n\n{content}")

    def _parse_response(self, response_text: str, task_type: TaskType) -> Dict:
        """Parse AI response into structured data"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)

        except json.JSONDecodeError:
            # Fallback: return raw text
            logger.warning(f"Failed to parse JSON for {task_type}, returning raw text")
            return {
                "raw_response": response_text,
                "parsed": False
            }

    def _calculate_confidence(self, result: Dict, task_type: TaskType) -> float:
        """Calculate confidence score for result"""
        # Check if response has explicit confidence
        if isinstance(result, dict):
            if "confidence" in result:
                return float(result["confidence"])
            if "overall_sentiment" in result and "confidence" in result["overall_sentiment"]:
                return float(result["overall_sentiment"]["confidence"])

        # Default confidence based on whether parsing succeeded
        if result.get("parsed", True):
            return 0.85
        return 0.5

    # ========================================================================
    # High-Level AI Services
    # ========================================================================

    async def analyze_meeting_comprehensive(
        self,
        transcript: str,
        screenshots: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive meeting analysis using multiple AI models
        Returns all insights in one go
        """
        # Run multiple analyses in parallel
        tasks = [
            self.process_task(TaskType.SUMMARY_GENERATION, transcript, metadata),
            self.process_task(TaskType.SENTIMENT_ANALYSIS, transcript, metadata),
            self.process_task(TaskType.ACTION_EXTRACTION, transcript, metadata),
            self.process_task(TaskType.DECISION_EXTRACTION, transcript, metadata),
            self.process_task(TaskType.TOPIC_CLASSIFICATION, transcript, metadata),
            self.process_task(TaskType.MEETING_SCORING, transcript, metadata),
        ]

        results = await asyncio.gather(*tasks)

        # Combine results
        comprehensive_analysis = {
            "summary": results[0].result if results[0].success else None,
            "sentiment": results[1].result if results[1].success else None,
            "action_items": results[2].result if results[2].success else None,
            "decisions": results[3].result if results[3].success else None,
            "topics": results[4].result if results[4].success else None,
            "quality_score": results[5].result if results[5].success else None,
            "metadata": {
                "models_used": [r.model for r in results if r.success],
                "total_tokens": sum(r.tokens_used for r in results),
                "processing_time": sum(r.processing_time for r in results),
                "average_confidence": sum(r.confidence for r in results) / len(results)
            }
        }

        return comprehensive_analysis

    async def transcribe_audio(self, audio_file_path: str) -> Dict:
        """Transcribe audio using Whisper API"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"]
                )

            return {
                "success": True,
                "text": transcript.text,
                "segments": transcript.segments if hasattr(transcript, 'segments') else [],
                "language": transcript.language if hasattr(transcript, 'language') else "en",
                "duration": transcript.duration if hasattr(transcript, 'duration') else None
            }

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_screenshot(
        self,
        image_path: str,
        context: Optional[str] = None
    ) -> Dict:
        """Analyze screenshot using vision models"""
        result = await self.process_task(
            TaskType.SCREENSHOT_ANALYSIS,
            f"Image analysis requested. Context: {context or 'Meeting screenshot'}",
            {"image_path": image_path}
        )

        return result.result if result.success else {"error": result.error}


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()
