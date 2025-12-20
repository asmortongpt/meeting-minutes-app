# backend-enhanced/analytics/metrics.py
"""
Analytics and Metrics Module for Meeting Trends and Team Productivity.

This module provides comprehensive analytics for meeting trends, team productivity metrics,
predictive machine learning models for meeting optimization, and ROI calculations for
meeting investments. It includes data processing, visualization preparation, and secure
data handling practices.

Key Features:
- Meeting trends analysis (duration, frequency, participation)
- Team productivity metrics (engagement scores, output correlation)
- Predictive ML models for meeting optimization
- ROI calculator for meeting-related investments
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import os
from abc import ABC, abstractmethod

# Configure logging for analytics module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsError(Exception):
    """Custom exception for analytics-related errors."""
    pass

class MetricsAnalyzer(ABC):
    """Abstract base class for metrics analysis."""
    
    @abstractmethod
    def calculate_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        pass

class MeetingTrendsAnalyzer(MetricsAnalyzer):
    """
    Analyzer for meeting trends including duration, frequency, and participation metrics.
    Provides insights into how meetings are conducted over time.
    """
    
    def __init__(self, data_source: str):
        """
        Initialize the MeetingTrendsAnalyzer with a data source path.
        
        Args:
            data_source (str): Path to the meeting data CSV/JSON file.
        """
        self.data_source = data_source
        self.data = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        Load meeting data from the specified source with error handling.
        
        Returns:
            pd.DataFrame: Loaded and cleaned meeting data.
        """
        try:
            if self.data_source.endswith('.csv'):
                df = pd.read_csv(self.data_source)
            elif self.data_source.endswith('.json'):
                df = pd.read_json(self.data_source)
            else:
                raise AnalyticsError("Unsupported data format. Use CSV or JSON.")
            
            # Validate required columns
            required_columns = ['start_time', 'end_time', 'participants', 'team_id']
            if not all(col in df.columns for col in required_columns):
                raise AnalyticsError("Missing required columns in data source.")
            
            # Convert datetime columns
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['end_time'] = pd.to_datetime(df['end_time'])
            df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60.0
            return df
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise AnalyticsError(f"Failed to load data: {str(e)}")

    def calculate_metrics(self, data: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Calculate key meeting trend metrics.
        
        Args:
            data (Optional[pd.DataFrame]): Optional DataFrame to analyze. Uses self.data if None.
            
        Returns:
            Dict[str, float]: Dictionary of calculated metrics.
        """
        try:
            df = data if data is not None else self.data
            if df.empty:
                raise AnalyticsError("No data available for trend analysis.")
                
            metrics = {
                'avg_meeting_duration': df['duration'].mean(),
                'total_meetings': len(df),
                'avg_participants': df['participants'].apply(lambda x: len(eval(x) if isinstance(x, str) else x)).mean(),
                'meetings_per_week': len(df) / ((df['start_time'].max() - df['start_time'].min()).days / 7)
            }
            return metrics
        except Exception as e:
            logger.error(f"Error calculating meeting trends: {str(e)}")
            raise AnalyticsError(f"Failed to calculate meeting trends: {str(e)}")

class TeamProductivityAnalyzer(MetricsAnalyzer):
    """
    Analyzer for team productivity metrics including engagement and output correlation.
    """
    
    def __init__(self, meeting_data: pd.DataFrame, output_data: pd.DataFrame):
        """
        Initialize with meeting and output data for productivity analysis.
        
        Args:
            meeting_data (pd.DataFrame): DataFrame containing meeting information.
            output_data (pd.DataFrame): DataFrame containing team output metrics.
        """
        self.meeting_data = meeting_data
        self.output_data = output_data

    def calculate_metrics(self, data: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Calculate team productivity metrics.
        
        Args:
            data (Optional[pd.DataFrame]): Optional DataFrame to analyze.
            
        Returns:
            Dict[str, float]: Dictionary of productivity metrics.
        """
        try:
            # Merge meeting and output data on team_id
            merged_data = pd.merge(
                self.meeting_data,
                self.output_data,
                on='team_id',
                how='inner'
            )
            
            if merged_data.empty:
                raise AnalyticsError("No matching data for productivity analysis.")
                
            # Calculate engagement score (simplified as meeting participation rate)
            engagement_score = merged_data.groupby('team_id')['participants'].apply(
                lambda x: x.apply(lambda p: len(eval(p) if isinstance(p, str) else p)).mean()
            ).mean()
            
            # Correlation between meeting duration and output
            correlation = merged_data['duration'].corr(merged_data.get('output_score', pd.Series(0)))
            
            return {
                'engagement_score': engagement_score,
                'meeting_output_correlation': correlation
            }
        except Exception as e:
            logger.error(f"Error calculating productivity metrics: {str(e)}")
            raise AnalyticsError(f"Failed to calculate productivity metrics: {str(e)}")

class PredictiveMeetingOptimizer:
    """
    Machine Learning model for predicting optimal meeting parameters.
    Uses historical data to predict meeting duration and participant impact.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False

    def train_model(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Train the ML model on historical meeting data.
        
        Args:
            X (np.ndarray): Feature matrix (duration, participants, etc.)
            y (np.ndarray): Target variable (e.g., meeting effectiveness score)
            
        Returns:
            float: Model performance score (R²)
        """
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True
            
            predictions = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, predictions)
            r2_score = self.model.score(X_test_scaled, y_test)
            
            logger.info(f"Model trained with MSE: {mse}, R²: {r2_score}")
            return r2_score
        except Exception as e:
            logger.error(f"Error training ML model: {str(e)}")
            raise AnalyticsError(f"Failed to train ML model: {str(e)}")

    def predict_optimal_parameters(self, input_data: np.ndarray) -> np.ndarray:
        """
        Predict optimal meeting parameters using the trained model.
        
        Args:
            input_data (np.ndarray): Input features for prediction.
            
        Returns:
            np.ndarray: Predicted optimal parameters.
        """
        if not self.is_trained:
            raise AnalyticsError("Model not trained. Call train_model first.")
            
        try:
            scaled_data = self.scaler.transform(input_data)
            predictions = self.model.predict(scaled_data)
            return predictions
        except Exception as e:
            logger.error(f"Error predicting optimal parameters: {str(e)}")
            raise AnalyticsError(f"Failed to predict optimal parameters: {str(e)}")

class ROICalculator:
    """
    Calculator for Return on Investment (ROI) for meeting-related expenses.
    """
    
    @staticmethod
    def calculate_roi(
        investment: float,
        returns: float,
        time_period_months: int = 12
    ) -> Dict[str, float]:
        """
        Calculate ROI for meeting investments.
        
        Args:
            investment (float): Total investment in meetings (tools, time, etc.)
            returns (float): Quantifiable returns from meetings (revenue, productivity gains)
            time_period_months (int): Time period for ROI calculation in months.
            
        Returns:
            Dict[str, float]: ROI metrics including percentage and annualized rate.
        """
        try:
            if investment <= 0:
                raise AnalyticsError("Investment must be greater than zero.")
                
            roi_percentage = ((returns - investment) / investment) * 100
            annualized_roi = roi_percentage * (12 / time_period_months)
            
            return {
                'roi_percentage': roi_percentage,
                'annualized_roi': annualized_roi,
                'net_return': returns - investment
            }
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            raise AnalyticsError(f"Failed to calculate ROI: {str(e)}")

def generate_dashboard_data(
    trends_analyzer: MeetingTrendsAnalyzer,
    productivity_analyzer: TeamProductivityAnalyzer,
    optimizer: PredictiveMeetingOptimizer
) -> Dict[str, any]:
    """
    Generate comprehensive data for the analytics dashboard.
    
    Args:
        trends_analyzer (MeetingTrendsAnalyzer): Analyzer for meeting trends.
        productivity_analyzer (TeamProductivityAnalyzer): Analyzer for productivity.
        optimizer (PredictiveMeetingOptimizer): ML optimizer for predictions.
        
    Returns:
        Dict[str, any]: Dashboard data including trends, productivity, and predictions.
    """
    try:
        dashboard_data = {
            'meeting_trends': trends_analyzer.calculate_metrics(),
            'productivity_metrics': productivity_analyzer.calculate_metrics(),
            'predictions': {
                'status': 'Model not trained' if not optimizer.is_trained else 'Model trained'
            },
            'timestamp': datetime.now().isoformat()
        }
        return dashboard_data
    except Exception as e:
        logger.error(f"Error generating dashboard data: {str(e)}")
        raise AnalyticsError(f"Failed to generate dashboard data: {str(e)}")

if __name__ == "__main__":
    # Example usage and testing
    try:
        # Dummy data for testing
        meeting_data = pd.DataFrame({
            'start_time': [datetime.now() - timedelta(days=i) for i in range(10)],
            'end_time': [datetime.now() - timedelta(days=i, hours=-1) for i in range(10)],
            'participants': ['["user1", "user2"]'] * 10,
            'team_id': [1] * 10,
            'duration': [60.0] * 10
        })
        output_data = pd.DataFrame({
            'team_id': [1] * 10,
            'output_score': [75.5] * 10
        })

        # Initialize analyzers
        trends_analyzer = MeetingTrendsAnalyzer("dummy_path.csv")
        trends_analyzer.data = meeting_data
        productivity_analyzer = TeamProductivityAnalyzer(meeting_data, output_data)
        optimizer = PredictiveMeetingOptimizer()

        # Generate dashboard data
        dashboard = generate_dashboard_data(trends_analyzer, productivity_analyzer, optimizer)
        logger.info(f"Dashboard Data: {json.dumps(dashboard, indent=2)}")

        # Test ROI calculation
        roi_metrics = ROICalculator.calculate_roi(10000.0, 15000.0, 6)
        logger.info(f"ROI Metrics: {json.dumps(roi_metrics, indent=2)}")

    except AnalyticsError as e:
        logger.error(f"Test failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during test: {str(e)}")