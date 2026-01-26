from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import logging
import os
import random

# Configure logging
logger = logging.getLogger(__name__)

class PredictionModel(ABC):
    """
    Abstract Base Class for all prediction models.
    Enforces a specific structure for any new model added in the future.
    """
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.load_model(model_path)

    @abstractmethod
    def load_model(self, model_path: str):
        """Load the trained model from disk."""
        pass

    @abstractmethod
    def predict(self, historical_data: list, steps_ahead: int) -> list:
        """
        Takes historical data and returns a list of dictionaries:
        [{'timestamp': '...', 'predicted_load': 123.4}, ...]
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        pass

    def _generate_mock_prediction(self, last_timestamp, steps_ahead):
        """
        Helper for beginners: If no real model file is found, return fake data
        so the app doesn't crash during testing.
        """
        predictions = []
        current_time = pd.to_datetime(last_timestamp)
        
        for i in range(steps_ahead):
            current_time += pd.Timedelta(minutes=1)
            # Generate a random load between 100 and 500
            pred_load = random.uniform(100, 500)
            predictions.append({
                "timestamp": current_time.isoformat(),
                "predicted_load": round(pred_load, 2)
            })
        return predictions

# --- Implementations ---

class ARIMAPredictor(PredictionModel):
    def get_model_name(self):
        return "ARIMA (AutoRegressive Integrated Moving Average)"

    def load_model(self, model_path):
        if os.path.exists(model_path):
            try:
                import statsmodels.api as sm
                self.model = sm.load(model_path)
                logger.info(f"Loaded ARIMA model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load ARIMA model: {e}")
        else:
            logger.warning(f"ARIMA model not found at {model_path}. Running in MOCK mode.")

    def predict(self, historical_data, steps_ahead):
        # Sort data by timestamp
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        last_ts = df['timestamp'].iloc[-1]

        if self.model:
            # Real prediction logic would go here using self.model.forecast()
            # This usually requires specific preprocessing
            pass
        
        # For this example, we fallback to mock generation if model isn't fully set up
        return self._generate_mock_prediction(last_ts, steps_ahead)


class ProphetPredictor(PredictionModel):
    def get_model_name(self):
        return "Facebook Prophet"

    def load_model(self, model_path):
        # Prophet requires specific installation. 
        # Logic is similar: check file existence, load if present.
        if os.path.exists(model_path):
            logger.info(f"Loaded Prophet model from {model_path}")
            # self.model = ...
        else:
            logger.warning(f"Prophet model not found at {model_path}. Running in MOCK mode.")

    def predict(self, historical_data, steps_ahead):
        df = pd.DataFrame(historical_data)
        last_ts = pd.to_datetime(df['timestamp'].iloc[-1])
        return self._generate_mock_prediction(last_ts, steps_ahead)


class LSTMPredictor(PredictionModel):
    def get_model_name(self):
        return "LSTM (Long Short-Term Memory)"

    def load_model(self, model_path):
        if os.path.exists(model_path):
            logger.info(f"Loaded LSTM model from {model_path}")
            # from tensorflow.keras.models import load_model
            # self.model = load_model(model_path)
        else:
            logger.warning(f"LSTM model not found at {model_path}. Running in MOCK mode.")

    def predict(self, historical_data, steps_ahead):
        df = pd.DataFrame(historical_data)
        last_ts = pd.to_datetime(df['timestamp'].iloc[-1])
        return self._generate_mock_prediction(last_ts, steps_ahead)


# --- Factory Function ---

def get_predictor(model_type: str) -> PredictionModel:
    """
    Factory to instantiate the correct model based on string input.
    """
    # In a real app, read paths from config.yaml
    paths = {
        "arima": "saved_models/arima_model.pkl",
        "prophet": "saved_models/prophet_model.pkl",
        "lstm": "saved_models/lstm_model.h5"
    }

    if model_type.lower() == "arima":
        return ARIMAPredictor(paths["arima"])
    elif model_type.lower() == "prophet":
        return ProphetPredictor(paths["prophet"])
    elif model_type.lower() == "lstm":
        return LSTMPredictor(paths["lstm"])
    else:
        raise ValueError(f"Unknown model type: {model_type}")
