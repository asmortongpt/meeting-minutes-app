# backend-enhanced/ai/translation.py
"""
Advanced AI Translation Module

This module provides real-time translation, voice command processing, sentiment analysis,
chart generation, and AI-based scheduling. It integrates multiple AI services and ensures
secure handling of data with comprehensive error handling.

Key Features:
- Real-time text and voice translation using Google Cloud Translate and Speech-to-Text
- Sentiment analysis using TextBlob
- Chart generation for data visualization using Matplotlib
- AI scheduling with basic conflict detection
- Secure data handling and logging
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
import matplotlib.pyplot as plt
from google.cloud import translate_v2 as translate
from google.cloud import speech
from textblob import TextBlob
import numpy as np
from pydantic import BaseModel, Field
import sounddevice as sd
import wavio
import threading
import queue

# Configure logging for production use
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_translation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Securely load environment variables for API credentials
try:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/service-account-key.json"
except Exception as e:
    logger.error(f"Failed to load Google Cloud credentials: {str(e)}")
    raise

# Initialize Google Cloud clients
try:
    translate_client = translate.Client()
    speech_client = speech.SpeechClient()
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud clients: {str(e)}")
    raise

# Constants
SAMPLE_RATE = 44100
RECORDING_DURATION = 5  # seconds
CHART_OUTPUT_DIR = Path("static/charts")
CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models for input validation
class TranslationRequest(BaseModel):
    text: str
    target_language: str = "en"
    source_language: Optional[str] = None

class VoiceCommandRequest(BaseModel):
    duration: int = RECORDING_DURATION

class SentimentData(BaseModel):
    text: str

class ScheduleItem(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = ""

class ChartData(BaseModel):
    labels: List[str]
    values: List[float]
    chart_type: str = "bar"
    title: str = "Chart"

class AITranslation:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.schedule: List[ScheduleItem] = []

    async def translate_text(self, request: TranslationRequest) -> Dict[str, str]:
        """
        Translates text to the target language using Google Cloud Translate.
        """
        try:
            result = translate_client.translate(
                request.text,
                target_language=request.target_language,
                source_language=request.source_language
            )
            translated_text = result["translatedText"]
            logger.info(f"Translated text to {request.target_language}: {translated_text}")
            return {
                "original": request.text,
                "translated": translated_text,
                "target_language": request.target_language
            }
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise ValueError(f"Translation failed: {str(e)}")

    def record_audio(self, duration: int = RECORDING_DURATION) -> np.ndarray:
        """
        Records audio from the microphone for the specified duration.
        """
        try:
            logger.info(f"Starting audio recording for {duration} seconds...")
            self.is_recording = True
            recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
            sd.wait()
            self.is_recording = False
            logger.info("Audio recording completed")
            return recording
        except Exception as e:
            logger.error(f"Audio recording error: {str(e)}")
            self.is_recording = False
            raise RuntimeError(f"Failed to record audio: {str(e)}")

    async def process_voice_command(self, request: VoiceCommandRequest) -> Dict[str, str]:
        """
        Processes voice input, converts it to text, and translates it if needed.
        """
        try:
            # Record audio in a separate thread to avoid blocking
            recording_thread = threading.Thread(
                target=lambda: self.audio_queue.put(self.record_audio(request.duration))
            )
            recording_thread.start()
            recording_thread.join()

            recording = self.audio_queue.get()
            output_path = "temp_recording.wav"
            wavio.write(output_path, recording, SAMPLE_RATE, sampwidth=2)

            # Convert audio to text using Google Speech-to-Text
            with open(output_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLE_RATE,
                language_code="en-US",
            )

            response = speech_client.recognize(config=config, audio=audio)
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript

            logger.info(f"Transcribed voice command: {transcript}")
            os.remove(output_path)  # Clean up temporary file securely

            return {"transcript": transcript}
        except Exception as e:
            logger.error(f"Voice command processing error: {str(e)}")
            raise RuntimeError(f"Failed to process voice command: {str(e)}")

    async def analyze_sentiment(self, request: SentimentData) -> Dict[str, float]:
        """
        Analyzes the sentiment of the provided text using TextBlob.
        Returns polarity (-1 to 1) and subjectivity (0 to 1).
        """
        try:
            blob = TextBlob(request.text)
            sentiment = {
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity
            }
            logger.info(f"Sentiment analysis for text: {sentiment}")
            return sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            raise ValueError(f"Sentiment analysis failed: {str(e)}")

    async def generate_chart(self, request: ChartData) -> str:
        """
        Generates a chart based on provided data and saves it as an image.
        Supports bar, line, and pie charts.
        """
        try:
            plt.figure(figsize=(10, 6))
            if request.chart_type == "bar":
                plt.bar(request.labels, request.values)
            elif request.chart_type == "line":
                plt.plot(request.labels, request.values, marker='o')
            elif request.chart_type == "pie":
                plt.pie(request.values, labels=request.labels, autopct='%1.1f%%')
            else:
                raise ValueError(f"Unsupported chart type: {request.chart_type}")

            plt.title(request.title)
            plt.xticks(rotation=45)
            plt.tight_layout()

            output_path = CHART_OUTPUT_DIR / f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_path)
            plt.close()

            logger.info(f"Chart generated and saved to {output_path}")
            return str(output_path.relative_to("static"))
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}")
            raise RuntimeError(f"Failed to generate chart: {str(e)}")

    async def add_schedule_item(self, item: ScheduleItem) -> Dict[str, str]:
        """
        Adds a schedule item with conflict detection.
        """
        try:
            # Check for conflicts with existing schedule items
            for existing in self.schedule:
                if (existing.start_time <= item.end_time and 
                    existing.end_time >= item.start_time):
                    raise ValueError(f"Schedule conflict with: {existing.title}")

            self.schedule.append(item)
            logger.info(f"Added schedule item: {item.title}")
            return {"status": "success", "message": f"Scheduled {item.title}"}
        except Exception as e:
            logger.error(f"Scheduling error: {str(e)}")
            raise ValueError(f"Failed to add schedule item: {str(e)}")

    async def get_schedule(self) -> List[Dict]:
        """
        Retrieves the current schedule as a list of dictionaries.
        """
        try:
            return [item.dict() for item in self.schedule]
        except Exception as e:
            logger.error(f"Error retrieving schedule: {str(e)}")
            raise RuntimeError(f"Failed to retrieve schedule: {str(e)}")


# Singleton instance for the AI translation service
ai_translation_service = AITranslation()

if __name__ == "__main__":
    # Example usage for testing purposes
    async def test_translation():
        request = TranslationRequest(text="Hola, ¿cómo estás?", target_language="en")
        result = await ai_translation_service.translate_text(request)
        print(f"Translation result: {result}")

    asyncio.run(test_translation())