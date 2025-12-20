"""
Multi-Model AI Orchestration System
Automatic failover, load balancing, and intelligent model selection
"""
import anthropic
import openai
from google import generativeai as genai
import logging
import time
import asyncio
from typing import Optional, Dict, List, Any, Literal
from dataclasses import dataclass
from enum import Enum
import os
from config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelType(str, Enum):
    """AI model categories"""
    VISION = "vision"
    AUDIO = "audio"
    ANALYSIS = "analysis"
    SUMMARY = "summary"
    CODE = "code"


class ModelProvider(str, Enum):
    """AI providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    provider: ModelProvider
    model_id: str
    max_tokens: int
    temperature: float = 0.7
    cost_per_1k_tokens: float = 0.01
    speed_score: int = 5  # 1-10, higher is faster
    quality_score: int = 5  # 1-10, higher is better
    is_available: bool = True


# Model registry with primary, fallback, and backup options
MODEL_REGISTRY: Dict[ModelType, List[ModelConfig]] = {
    ModelType.VISION: [
        ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.003,
            speed_score=8,
            quality_score=10
        ),
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-vision-preview",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.01,
            speed_score=6,
            quality_score=9
        ),
        ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_id="gemini-pro-vision",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.00025,
            speed_score=9,
            quality_score=8
        ),
    ],

    ModelType.AUDIO: [
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="whisper-1",
            max_tokens=0,  # Not applicable
            cost_per_1k_tokens=0.006,
            speed_score=7,
            quality_score=10
        ),
    ],

    ModelType.ANALYSIS: [
        ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.5,
            cost_per_1k_tokens=0.015,
            speed_score=6,
            quality_score=10
        ),
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-turbo-preview",
            max_tokens=4096,
            temperature=0.5,
            cost_per_1k_tokens=0.01,
            speed_score=8,
            quality_score=9
        ),
        ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_id="gemini-1.5-pro-latest",
            max_tokens=8192,
            temperature=0.5,
            cost_per_1k_tokens=0.00125,
            speed_score=9,
            quality_score=8
        ),
    ],

    ModelType.SUMMARY: [
        ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-haiku-20240307",
            max_tokens=4096,
            temperature=0.3,
            cost_per_1k_tokens=0.00025,
            speed_score=10,
            quality_score=8
        ),
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo-16k",
            max_tokens=4096,
            temperature=0.3,
            cost_per_1k_tokens=0.0015,
            speed_score=9,
            quality_score=7
        ),
        ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_id="gemini-pro",
            max_tokens=4096,
            temperature=0.3,
            cost_per_1k_tokens=0.00025,
            speed_score=9,
            quality_score=7
        ),
    ],

    ModelType.CODE: [
        ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.0,
            cost_per_1k_tokens=0.003,
            speed_score=8,
            quality_score=10
        ),
        ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4",
            max_tokens=4096,
            temperature=0.0,
            cost_per_1k_tokens=0.03,
            speed_score=7,
            quality_score=9
        ),
    ],
}


# ============================================================================
# AI ORCHESTRATOR
# ============================================================================

class AIOrchestrator:
    """
    Multi-model AI orchestrator with automatic failover

    Features:
    - Automatic model selection based on task
    - Failover to backup models on error
    - Load balancing across providers
    - Cost tracking
    - Performance monitoring
    """

    def __init__(self):
        # Initialize API clients
        self.anthropic_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

        self.openai_client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Performance tracking
        self.request_count: Dict[str, int] = {}
        self.error_count: Dict[str, int] = {}
        self.total_cost: float = 0.0

        logger.info("🤖 AI Orchestrator initialized with multi-model support")

    async def generate(
        self,
        prompt: str,
        model_type: ModelType = ModelType.ANALYSIS,
        max_retries: int = 3,
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        max_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate response using best available model

        Args:
            prompt: Input prompt
            model_type: Type of task (vision, audio, analysis, etc.)
            max_retries: Maximum retry attempts
            prefer_speed: Prioritize fast models
            prefer_quality: Prioritize high-quality models
            max_cost: Maximum cost per request

        Returns:
            {
                "response": str,
                "model_used": str,
                "provider": str,
                "cost": float,
                "latency_ms": int
            }
        """

        # Get available models for this type
        models = self._select_models(
            model_type,
            prefer_speed=prefer_speed,
            prefer_quality=prefer_quality,
            max_cost=max_cost
        )

        if not models:
            raise ValueError(f"No available models for type: {model_type}")

        # Try each model until success
        last_error = None

        for model_config in models:
            try:
                logger.info(f"🎯 Trying {model_config.provider.value}/{model_config.model_id}")

                start_time = time.time()

                # Route to appropriate provider
                if model_config.provider == ModelProvider.ANTHROPIC:
                    response = await self._generate_anthropic(prompt, model_config)
                elif model_config.provider == ModelProvider.OPENAI:
                    response = await self._generate_openai(prompt, model_config)
                elif model_config.provider == ModelProvider.GOOGLE:
                    response = await self._generate_google(prompt, model_config)
                else:
                    continue

                latency_ms = int((time.time() - start_time) * 1000)

                # Track metrics
                self._track_success(model_config)

                result = {
                    "response": response,
                    "model_used": model_config.model_id,
                    "provider": model_config.provider.value,
                    "cost": self._estimate_cost(prompt, response, model_config),
                    "latency_ms": latency_ms,
                    "success": True
                }

                logger.info(
                    f"✅ Success! Model: {model_config.model_id}, "
                    f"Latency: {latency_ms}ms, Cost: ${result['cost']:.4f}"
                )

                return result

            except Exception as e:
                logger.warning(
                    f"⚠️  Model {model_config.model_id} failed: {str(e)}"
                )
                self._track_error(model_config)
                last_error = e
                continue

        # All models failed
        raise RuntimeError(
            f"All models failed for {model_type}. Last error: {last_error}"
        )

    async def _generate_anthropic(
        self,
        prompt: str,
        config: ModelConfig
    ) -> str:
        """Generate using Anthropic Claude"""

        message = self.anthropic_client.messages.create(
            model=config.model_id,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return message.content[0].text

    async def _generate_openai(
        self,
        prompt: str,
        config: ModelConfig
    ) -> str:
        """Generate using OpenAI GPT"""

        response = self.openai_client.chat.completions.create(
            model=config.model_id,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )

        return response.choices[0].message.content

    async def _generate_google(
        self,
        prompt: str,
        config: ModelConfig
    ) -> str:
        """Generate using Google Gemini"""

        model = genai.GenerativeModel(config.model_id)

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=config.max_tokens,
                temperature=config.temperature,
            )
        )

        return response.text

    def _select_models(
        self,
        model_type: ModelType,
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        max_cost: Optional[float] = None
    ) -> List[ModelConfig]:
        """Select and sort models based on preferences"""

        models = MODEL_REGISTRY.get(model_type, [])

        # Filter by availability and cost
        available = [
            m for m in models
            if m.is_available and (
                max_cost is None or m.cost_per_1k_tokens <= max_cost
            )
        ]

        if not available:
            return []

        # Sort by preference
        if prefer_speed:
            available.sort(key=lambda m: m.speed_score, reverse=True)
        elif prefer_quality:
            available.sort(key=lambda m: m.quality_score, reverse=True)
        else:
            # Default: balance of quality and speed
            available.sort(
                key=lambda m: (m.quality_score + m.speed_score) / 2,
                reverse=True
            )

        return available

    def _track_success(self, config: ModelConfig):
        """Track successful request"""
        key = f"{config.provider.value}/{config.model_id}"
        self.request_count[key] = self.request_count.get(key, 0) + 1

    def _track_error(self, config: ModelConfig):
        """Track failed request"""
        key = f"{config.provider.value}/{config.model_id}"
        self.error_count[key] = self.error_count.get(key, 0) + 1

    def _estimate_cost(
        self,
        prompt: str,
        response: str,
        config: ModelConfig
    ) -> float:
        """Estimate cost of request"""
        # Rough token estimation (4 chars per token)
        total_tokens = (len(prompt) + len(response)) / 4
        cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        self.total_cost += cost
        return cost

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "total_requests": sum(self.request_count.values()),
            "total_errors": sum(self.error_count.values()),
            "total_cost_usd": round(self.total_cost, 4),
            "requests_by_model": self.request_count,
            "errors_by_model": self.error_count,
            "success_rate": self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())

        if total_requests + total_errors == 0:
            return 1.0

        return total_requests / (total_requests + total_errors)


# Global orchestrator instance
orchestrator = AIOrchestrator()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def analyze_meeting(meeting_content: str) -> Dict[str, Any]:
    """Analyze meeting content for insights"""

    prompt = f"""Analyze this meeting transcript and provide:

1. **Executive Summary** (3 bullet points max)
2. **Key Decisions Made** (list with rationale)
3. **Action Items** (extract specific tasks with owners)
4. **Discussion Topics** (main themes)
5. **Sentiment Analysis** (overall team mood: positive/neutral/negative)
6. **Follow-up Suggestions** (what should happen next)

Meeting Content:
{meeting_content}

Return as JSON with keys: summary, decisions, action_items, topics, sentiment, follow_ups
"""

    return await orchestrator.generate(
        prompt,
        model_type=ModelType.ANALYSIS,
        prefer_quality=True
    )


async def summarize_meeting(meeting_content: str, max_length: int = 200) -> str:
    """Generate concise meeting summary"""

    prompt = f"""Summarize this meeting in {max_length} words or less. Focus on:
- Key decisions
- Important action items
- Main discussion points

Meeting:
{meeting_content}
"""

    result = await orchestrator.generate(
        prompt,
        model_type=ModelType.SUMMARY,
        prefer_speed=True
    )

    return result["response"]


async def extract_action_items(text: str) -> List[Dict[str, str]]:
    """Extract action items from text"""

    prompt = f"""Extract all action items from this text.

For each action item, identify:
- description: What needs to be done
- owner: Who is responsible (if mentioned)
- due_date: When it's due (if mentioned)
- priority: high/medium/low (infer from context)

Return as JSON array of objects.

Text:
{text}
"""

    result = await orchestrator.generate(
        prompt,
        model_type=ModelType.ANALYSIS,
        prefer_speed=True,
        max_cost=0.01
    )

    import json
    try:
        return json.loads(result["response"])
    except:
        return []


async def identify_speakers(transcript: str) -> Dict[str, List[str]]:
    """Identify unique speakers and their contributions"""

    prompt = f"""Analyze this transcript and identify unique speakers.

For each speaker:
- Extract their name/identifier
- List their main contributions
- Count their speaking turns

Return as JSON.

Transcript:
{transcript}
"""

    result = await orchestrator.generate(
        prompt,
        model_type=ModelType.ANALYSIS
    )

    import json
    try:
        return json.loads(result["response"])
    except:
        return {}
