# backend-enhanced/ai/voice_commands.py
"""
Voice Commands Module for AI-Powered Assistant

This module handles voice command processing with real-time translation,
sentiment analysis, chart generation, and AI-based scheduling. It integrates
with various AI models and external APIs for comprehensive functionality.

Key Features:
- Voice-to-text conversion with error handling
- Real-time language translation
- Sentiment analysis of user input
- Dynamic chart generation for data visualization
- AI-driven scheduling and calendar management
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import speech_recognition as sr
from googletrans import Translator
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import json
from pathlib import Path
import wave
import pyaudio

# Configure logging for production environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voice_commands.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
except Exception as e:
    logger.error(f"Failed to download NLTK data: {str(e)}")

# Constants for security and configuration
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
MAX_RETRIES = 3
SCOPES = ['https://www.googleapis.com/auth/calendar']

class VoiceCommandProcessor:
    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize the Voice Command Processor with necessary configurations.
        
        Args:
            credentials_path (str): Path to Google API credentials JSON
            token_path (str): Path to token pickle file for Google Calendar API
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.translator = Translator()
        self.sid = SentimentIntensityAnalyzer()
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.calendar_service = self._initialize_calendar_service()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=5)
            logger.info("Adjusted for ambient noise")

    def _initialize_calendar_service(self) -> Any:
        """
        Initialize Google Calendar API service with OAuth2 credentials.
        
        Returns:
            Any: Google Calendar API service object
        """
        try:
            creds = None
            token_file = Path(self.token_path)
            if token_file.exists():
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize calendar service: {str(e)}")
            raise

    async def record_audio(self, duration: int = RECORD_SECONDS) -> Optional[bytes]:
        """
        Record audio from microphone for specified duration.
        
        Args:
            duration (int): Duration to record in seconds
            
        Returns:
            Optional[bytes]: Recorded audio data or None if failed
        """
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            logger.info("Recording audio...")
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
                
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            return b''.join(frames)
        except Exception as e:
            logger.error(f"Error recording audio: {str(e)}")
            return None

    async def voice_to_text(self, audio_data: bytes) -> Optional[str]:
        """
        Convert recorded audio to text using speech recognition.
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            # Convert raw audio data to AudioData object
            with wave.open(BytesIO(audio_data), 'wb') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)
                wav_file.setframerate(RATE)
                wav_file.writeframes(audio_data)
                
            audio = sr.AudioData(audio_data, RATE, 2)
            for attempt in range(MAX_RETRIES):
                try:
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Transcribed text: {text}")
                    return text
                except sr.WaitTimeoutError:
                    logger.warning("Speech recognition timeout, retrying...")
                    continue
                except sr.UnknownValueError:
                    logger.warning("Could not understand audio, retrying...")
                    continue
                except sr.RequestError as e:
                    logger.error(f"Speech recognition API error: {str(e)}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error in voice to text conversion: {str(e)}")
            return None

    async def translate_text(self, text: str, target_lang: str = 'en') -> Optional[str]:
        """
        Translate text to target language using Google Translate.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            
        Returns:
            Optional[str]: Translated text or None if failed
        """
        try:
            translated = self.translator.translate(text, dest=target_lang)
            logger.info(f"Translated text to {target_lang}: {translated.text}")
            return translated.text
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return None

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Perform sentiment analysis on the input text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        try:
            scores = self.sid.polarity_scores(text)
            logger.info(f"Sentiment analysis for text '{text}': {scores}")
            return scores
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return {"neg": 0.0, "neu": 0.0, "pos": 0.0, "compound": 0.0}

    async def generate_chart(self, data: List[float], labels: List[str], title: str) -> str:
        """
        Generate a base64-encoded chart image from data.
        
        Args:
            data (List[float]): Data points for chart
            labels (List[str]): Labels for data points
            title (str): Chart title
            
        Returns:
            str: Base64-encoded image string
        """
        try:
            plt.figure(figsize=(10, 6))
            plt.bar(labels, data)
            plt.title(title)
            plt.xlabel('Categories')
            plt.ylabel('Values')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            logger.info(f"Generated chart with title: {title}")
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}")
            return ""

    async def schedule_event(self, summary: str, start_time: datetime, end_time: datetime, 
                           description: str = "") -> Optional[Dict]:
        """
        Schedule an event in Google Calendar.
        
        Args:
            summary (str): Event title
            start_time (datetime): Start time of event
            end_time (datetime): End time of event
            description (str): Event description
            
        Returns:
            Optional[Dict]: Created event details or None if failed
        """
        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            event = self.calendar_service.events().insert(
                calendarId='primary', body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event
        except Exception as e:
            logger.error(f"Error scheduling event: {str(e)}")
            return None

    async def process_voice_command(self, duration: int = RECORD_SECONDS) -> Dict[str, Any]:
        """
        Process a complete voice command pipeline from recording to analysis.
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            Dict[str, Any]: Results containing transcribed text, translation,
                           sentiment, and any generated content
        """
        try:
            result = {
                "status": "error",
                "text": "",
                "translated_text": "",
                "sentiment": {},
                "chart": "",
                "event": None,
                "error": ""
            }
            
            # Record audio
            audio_data = await self.record_audio(duration)
            if not audio_data:
                result["error"] = "Failed to record audio"
                return result
                
            # Convert to text
            text = await self.voice_to_text(audio_data)
            if not text:
                result["error"] = "Failed to transcribe audio"
                return result
                
            result["text"] = text
            
            # Translate if needed
            translated = await self.translate_text(text)
            result["translated_text"] = translated or ""
            
            # Analyze sentiment
            sentiment = await self.analyze_sentiment(text)
            result["sentiment"] = sentiment
            
            # Example: Generate chart if command contains "chart"
            if "chart" in text.lower():
                data = [10, 20, 30, 40]
                labels = ["A", "B", "C", "D"]
                chart = await self.generate_chart(data, labels, "Sample Chart")
                result["chart"] = chart
            
            # Example: Schedule event if command contains "schedule"
            if "schedule" in text.lower():
                start_time = datetime.utcnow()
                end_time = datetime.utcnow()
                event = await self.schedule_event(
                    "Voice Command Event",
                    start_time,
                    end_time,
                    "Scheduled via voice command"
                )
                result["event"] = event
                
            result["status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            result["error"] = str(e)
            return result

if __name__ == "__main__":
    # Example usage
    processor = VoiceCommandProcessor(
        credentials_path="path/to/credentials.json",
        token_path="path/to/token.pickle"
    )
    
    async def main():
        result = await processor.process_voice_command()
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())