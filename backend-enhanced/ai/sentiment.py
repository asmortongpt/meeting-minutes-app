# backend-enhanced/ai/sentiment.py
"""
Sentiment Analysis Module with AI Enhancements

This module provides advanced sentiment analysis for text and voice input,
real-time translation, chart generation for visualization, and AI-based scheduling.
It integrates with external APIs for speech-to-text, translation, and sentiment scoring.
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import speechbrain as sb
from google.cloud import translate_v2 as translate
from google.cloud import speech
import torch
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import wave
import contextlib
import requests
from dotenv import load_dotenv

# Load environment variables for API keys and configurations
load_dotenv()

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='sentiment.log'
)
logger = logging.getLogger(__name__)

# Constants for API configurations and security
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SENTIMENT_API_URL = os.getenv("SENTIMENT_API_URL", "https://api.sentiment.example.com/analyze")
CHART_STORAGE_PATH = Path("static/charts")
AUDIO_STORAGE_PATH = Path("static/audio")
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB max audio file size

# Ensure storage directories exist
CHART_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
AUDIO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

class SentimentAnalyzer:
    """Class to handle sentiment analysis, voice processing, translation, and scheduling."""
    
    def __init__(self):
        """Initialize the SentimentAnalyzer with necessary models and clients."""
        try:
            # Initialize Google Cloud clients with credentials
            self.translate_client = translate.Client()
            self.speech_client = speech.SpeechClient()
            # Load pre-trained speech emotion recognition model
            self.emotion_classifier = sb.pretrained.EncoderClassifier.from_hparams(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                hparams_file="hyperparams.yaml",
                savedir="pretrained_models/emotion-recognition-wav2vec2-IEMOCAP"
            )
            # Initialize text sentiment model
            self.vectorizer = TfidfVectorizer(max_features=5000)
            self.model = LogisticRegression(max_iter=1000)
            self.is_trained = False
            logger.info("SentimentAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    def train_text_model(self, texts: List[str], labels: List[int]) -> None:
        """
        Train the text sentiment model with provided data.
        
        Args:
            texts: List of text samples for training.
            labels: List of corresponding sentiment labels (0 for negative, 1 for positive).
        """
        try:
            if len(texts) < 2 or len(labels) != len(texts):
                raise ValueError("Insufficient or mismatched training data")
            X = self.vectorizer.fit_transform(texts)
            self.model.fit(X, labels)
            self.is_trained = True
            logger.info("Text sentiment model trained successfully")
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise

    def analyze_text_sentiment(self, text: str, language: str = "en") -> Dict[str, any]:
        """
        Analyze sentiment of text input with optional translation.
        
        Args:
            text: Input text to analyze.
            language: Language code of the input text.
            
        Returns:
            Dictionary containing sentiment scores and metadata.
        """
        try:
            if not text.strip():
                raise ValueError("Empty text input")
                
            # Translate if not in English
            translated_text = text
            if language != "en":
                translated_text = self.translate_text(text, language, "en")
                
            # Use trained model if available, otherwise use external API
            if self.is_trained:
                features = self.vectorizer.transform([translated_text])
                score = self.model.predict_proba(features)[0][1]
                sentiment = "positive" if score > 0.5 else "negative"
            else:
                response = requests.post(
                    SENTIMENT_API_URL,
                    json={"text": translated_text},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                score = result.get("score", 0.5)
                sentiment = result.get("sentiment", "neutral")
                
            return {
                "original_text": text,
                "translated_text": translated_text,
                "sentiment": sentiment,
                "score": float(score),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Text sentiment analysis failed: {str(e)}")
            raise

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            
        Returns:
            Translated text.
        """
        try:
            result = self.translate_client.translate(
                text, source_language=source_lang, target_language=target_lang
            )
            return result["translatedText"]
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise

    def process_voice_input(self, audio_path: str) -> Dict[str, any]:
        """
        Process voice input for sentiment analysis.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            Dictionary containing voice sentiment analysis results.
        """
        try:
            audio_file = Path(audio_path)
            if not audio_file.exists() or audio_file.stat().st_size > MAX_AUDIO_SIZE:
                raise ValueError("Invalid or oversized audio file")
                
            # Convert audio to text using Google Speech-to-Text
            text = self.speech_to_text(audio_path)
            # Analyze emotional tone from voice
            emotion = self.analyze_voice_emotion(audio_path)
            # Analyze text sentiment
            text_analysis = self.analyze_text_sentiment(text)
            
            return {
                "text": text,
                "voice_emotion": emotion,
                "text_sentiment": text_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Voice input processing failed: {str(e)}")
            raise

    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text using Google Cloud Speech API.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            Transcribed text.
        """
        try:
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
                
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US"
            )
            response = self.speech_client.recognize(config=config, audio=audio)
            return " ".join([result.alternatives[0].transcript for result in response.results])
        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {str(e)}")
            raise

    def analyze_voice_emotion(self, audio_path: str) -> Dict[str, float]:
        """
        Analyze emotional tone from voice input.
        
        Args:
            audio_path: Path to the audio file.
            
        Returns:
            Dictionary of emotion scores.
        """
        try:
            # Load and process audio file
            signal, fs = torch.load(audio_path)
            # Classify emotion using pre-trained model
            output_probs, score, index, text_lab = self.emotion_classifier.classify_batch(signal)
            return {text_lab[i]: float(prob) for i, prob in enumerate(output_probs[0])}
        except Exception as e:
            logger.error(f"Voice emotion analysis failed: {str(e)}")
            raise

    def generate_sentiment_chart(self, data: List[Dict[str, any]], output_path: str) -> str:
        """
        Generate a sentiment trend chart.
        
        Args:
            data: List of sentiment analysis results.
            output_path: Path to save the chart.
            
        Returns:
            Path to the generated chart.
        """
        try:
            if not data:
                raise ValueError("No data provided for chart generation")
                
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)
            
            plt.figure(figsize=(10, 6))
            plt.plot(df.index, df["score"], marker="o", color="blue")
            plt.title("Sentiment Score Over Time")
            plt.xlabel("Time")
            plt.ylabel("Sentiment Score")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            full_path = str(CHART_STORAGE_PATH / output_path)
            plt.savefig(full_path)
            plt.close()
            logger.info(f"Chart generated at {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            raise

    def schedule_analysis(self, text: str, schedule_time: datetime) -> Dict[str, str]:
        """
        Schedule sentiment analysis for a future time using AI-based priority.
        
        Args:
            text: Text to analyze.
            schedule_time: Scheduled time for analysis.
            
        Returns:
            Dictionary with scheduling confirmation.
        """
        try:
            if schedule_time < datetime.utcnow():
                raise ValueError("Scheduled time must be in the future")
                
            # Simple AI-based priority (placeholder for more complex logic)
            priority = "high" if len(text.split()) > 50 else "normal"
            
            # Log scheduled task (in production, this would integrate with a task queue like Celery)
            logger.info(f"Scheduled analysis for {schedule_time.isoformat()} with priority {priority}")
            return {
                "status": "scheduled",
                "text": text,
                "scheduled_time": schedule_time.isoformat(),
                "priority": priority
            }
        except Exception as e:
            logger.error(f"Scheduling failed: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        analyzer = SentimentAnalyzer()
        # Example usage
        result = analyzer.analyze_text_sentiment("I love this product!", "en")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        print(f"Error: {str(e)}")