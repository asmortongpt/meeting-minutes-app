# backend-enhanced/analytics/predictions.py
"""
This module handles analytics and predictions for meeting trends, team productivity,
and ROI calculations using machine learning models. It integrates with the database
to fetch historical data and applies predictive algorithms for actionable insights.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import logging
from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

# Load environment variables for secure database connection
load_dotenv()

# Configure logging for monitoring and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='analytics_predictions.log'
)
logger = logging.getLogger(__name__)

# Database connection setup with environment variables for security
DB_USER = os.getenv('DB_USER', 'default_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'default_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'meeting_analytics')
DB_PORT = os.getenv('DB_PORT', '5432')

# Create a secure database connection string
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, echo=False)

class AnalyticsEngine:
    """Class to manage analytics and predictions for meeting and productivity data."""
    
    def __init__(self) -> None:
        """Initialize the AnalyticsEngine with default configurations."""
        self.model = LinearRegression()
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.last_updated: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)

    def fetch_meeting_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch historical meeting data from the database with error handling.
        
        Returns:
            Optional[pd.DataFrame]: DataFrame containing meeting data or None if fetch fails.
        """
        try:
            query = """
                SELECT meeting_id, start_time, end_time, duration_minutes, 
                       attendees_count, cost, productivity_score
                FROM meetings
                WHERE start_time >= NOW() - INTERVAL '6 months'
            """
            with engine.connect() as connection:
                df = pd.read_sql(query, connection)
                logger.info(f"Fetched {len(df)} meeting records from database.")
                return df
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching meeting data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching meeting data: {str(e)}")
            return None

    def fetch_team_productivity_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch team productivity data from the database.
        
        Returns:
            Optional[pd.DataFrame]: DataFrame containing productivity data or None if fetch fails.
        """
        try:
            query = """
                SELECT team_id, recorded_date, productivity_score, 
                       hours_worked, tasks_completed
                FROM team_productivity
                WHERE recorded_date >= NOW() - INTERVAL '6 months'
            """
            with engine.connect() as connection:
                df = pd.read_sql(query, connection)
                logger.info(f"Fetched {len(df)} productivity records from database.")
                return df
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching productivity data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching productivity data: {str(e)}")
            return None

    def update_data_cache(self) -> bool:
        """
        Update the data cache if it's outdated or empty.
        
        Returns:
            bool: True if cache update is successful, False otherwise.
        """
        current_time = datetime.now()
        if self.last_updated is None or (current_time - self.last_updated) > self.cache_duration:
            meeting_data = self.fetch_meeting_data()
            productivity_data = self.fetch_team_productivity_data()
            
            if meeting_data is not None and productivity_data is not None:
                self.data_cache['meetings'] = meeting_data
                self.data_cache['productivity'] = productivity_data
                self.last_updated = current_time
                logger.info("Data cache updated successfully.")
                return True
            return False
        return True

    def calculate_meeting_trends(self) -> Dict[str, any]:
        """
        Analyze meeting trends over the past 6 months.
        
        Returns:
            Dict[str, any]: Dictionary containing trend metrics.
        """
        if not self.update_data_cache() or 'meetings' not in self.data_cache:
            logger.error("Failed to update data cache for meeting trends.")
            return {"error": "Data unavailable"}

        df = self.data_cache['meetings']
        if df.empty:
            return {"error": "No meeting data available"}

        # Group by month for trend analysis
        df['month'] = df['start_time'].dt.to_period('M')
        monthly_trends = df.groupby('month').agg({
            'duration_minutes': 'mean',
            'attendees_count': 'mean',
            'cost': 'sum',
            'productivity_score': 'mean'
        }).reset_index()

        return {
            "monthly_avg_duration": monthly_trends['duration_minutes'].tolist(),
            "monthly_avg_attendees": monthly_trends['attendees_count'].tolist(),
            "monthly_total_cost": monthly_trends['cost'].tolist(),
            "monthly_avg_productivity": monthly_trends['productivity_score'].tolist(),
            "months": monthly_trends['month'].astype(str).tolist()
        }

    def train_predictive_model(self, data: pd.DataFrame, target: str) -> Tuple[float, float]:
        """
        Train a linear regression model for predictions.
        
        Args:
            data (pd.DataFrame): Input DataFrame with features and target.
            target (str): Target column for prediction.
            
        Returns:
            Tuple[float, float]: Model accuracy (R2 score) and RMSE.
        """
        try:
            X = data.drop(columns=[target])
            y = data[target]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            self.model.fit(X_train, y_train)
            predictions = self.model.predict(X_test)
            r2_score = self.model.score(X_test, y_test)
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            
            logger.info(f"Model trained for {target} with R2: {r2_score}, RMSE: {rmse}")
            return r2_score, rmse
        except Exception as e:
            logger.error(f"Error training predictive model: {str(e)}")
            return 0.0, 0.0

    def predict_meeting_cost(self, duration: float, attendees: int) -> float:
        """
        Predict meeting cost based on historical data.
        
        Args:
            duration (float): Meeting duration in minutes.
            attendees (int): Number of attendees.
            
        Returns:
            float: Predicted cost of the meeting.
        """
        if 'meetings' not in self.data_cache or self.data_cache['meetings'].empty:
            self.update_data_cache()
        
        df = self.data_cache.get('meetings', pd.DataFrame())
        if df.empty:
            logger.error("No meeting data available for cost prediction.")
            return 0.0

        # Prepare data for training
        features = df[['duration_minutes', 'attendees_count']]
        target = df['cost']
        data_for_training = pd.concat([features, target], axis=1)
        
        self.train_predictive_model(data_for_training, 'cost')
        predicted_cost = self.model.predict([[duration, attendees]])[0]
        return max(0.0, predicted_cost)  # Ensure non-negative cost

    def calculate_roi(self, meeting_cost: float, productivity_gain: float) -> float:
        """
        Calculate Return on Investment (ROI) for meetings.
        
        Args:
            meeting_cost (float): Total cost of the meeting.
            productivity_gain (float): Estimated productivity gain in monetary terms.
            
        Returns:
            float: ROI percentage.
        """
        try:
            if meeting_cost <= 0:
                logger.warning("Meeting cost is zero or negative, ROI undefined.")
                return 0.0
            roi = (productivity_gain - meeting_cost) / meeting_cost * 100
            logger.info(f"Calculated ROI: {roi}% for cost: {meeting_cost}, gain: {productivity_gain}")
            return round(roi, 2)
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0

    def get_team_productivity_metrics(self) -> Dict[str, any]:
        """
        Calculate team productivity metrics.
        
        Returns:
            Dict[str, any]: Dictionary containing productivity metrics.
        """
        if not self.update_data_cache() or 'productivity' not in self.data_cache:
            logger.error("Failed to update data cache for productivity metrics.")
            return {"error": "Data unavailable"}

        df = self.data_cache['productivity']
        if df.empty:
            return {"error": "No productivity data available"}

        metrics = df.groupby('team_id').agg({
            'productivity_score': 'mean',
            'hours_worked': 'sum',
            'tasks_completed': 'sum'
        }).reset_index()

        return {
            "team_ids": metrics['team_id'].tolist(),
            "avg_productivity": metrics['productivity_score'].tolist(),
            "total_hours": metrics['hours_worked'].tolist(),
            "total_tasks": metrics['tasks_completed'].tolist()
        }

def get_analytics_instance() -> AnalyticsEngine:
    """
    Singleton factory method to get an instance of AnalyticsEngine.
    
    Returns:
        AnalyticsEngine: Instance of the analytics engine.
    """
    if not hasattr(get_analytics_instance, 'instance'):
        get_analytics_instance.instance = AnalyticsEngine()
    return get_analytics_instance.instance

if __name__ == "__main__":
    # Example usage for testing purposes
    analytics = get_analytics_instance()
    trends = analytics.calculate_meeting_trends()
    productivity = analytics.get_team_productivity_metrics()
    predicted_cost = analytics.predict_meeting_cost(60.0, 5)
    roi = analytics.calculate_roi(predicted_cost, 1000.0)
    
    logger.info(f"Meeting Trends: {json.dumps(trends, indent=2)}")
    logger.info(f"Productivity Metrics: {json.dumps(productivity, indent=2)}")
    logger.info(f"Predicted Meeting Cost: {predicted_cost}")
    logger.info(f"Calculated ROI: {roi}%")