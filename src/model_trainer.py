"""
================================================================================
FILE: src/model_trainer.py
ROLE: M2 (Modeler / AI Engineer)
PURPOSE: Train AI models to predict future HTTP traffic.
================================================================================

This script implements what M2 (Modeler) does:
1. Load the clean data from M1
2. Train a time-series forecasting model (ARIMA)
3. Evaluate the model using standard metrics (RMSE, MAE, MAPE)
4. Save the trained model for the API to use

WHAT IS TIME-SERIES FORECASTING?
---------------------------------
Time-series = Data points collected over time (like daily stock prices).
Forecasting = Predicting future values based on past patterns.

Example: If website traffic was [100, 120, 110, 130] in the last 4 hours,
we want to predict what it will be in the next hour.

WHAT IS ARIMA?
--------------
ARIMA = AutoRegressive Integrated Moving Average

It's a statistical model with 3 components:
- AR (AutoRegressive): Uses past values to predict future.
  "If yesterday was busy, today might be busy too."
  
- I (Integrated): Handles trends by differencing.
  "Traffic is generally increasing week over week."
  
- MA (Moving Average): Uses past prediction errors.
  "Our model was wrong by +50 yesterday, so adjust today."

The model has 3 parameters: ARIMA(p, d, q)
- p = Number of past values to use (lag order)
- d = Number of times to difference the data (trend removal)
- q = Number of past errors to use (moving average order)

We use ARIMA(5, 1, 0) which means:
- Look at the last 5 values
- Difference once (remove trend)
- Don't use moving average (keep it simple)

WHY NOT USE DEEP LEARNING (LSTM)?
---------------------------------
The competition says "hạn chế deeplearning nếu có thể" (limit deep learning).
ARIMA is:
- Faster to train (seconds vs hours)
- Easier to explain to judges
- Requires no GPU
- Good enough for this problem

USAGE:
------
    cd uibackend
    python src/model_trainer.py

OUTPUT:
-------
    saved_models/arima_model.pkl - The trained model

================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

# pandas: Data manipulation (loading CSV, handling DataFrames)
import pandas as pd

# numpy: Numerical operations (math functions, arrays)
import numpy as np

# pickle: Saves Python objects to files (serialization)
# We use this to save the trained model so the API can load it later.
import pickle

# os: Operating system interface (file paths, directory creation)
import os

# time: For measuring how long training takes
import time

# datetime: For timestamping when the model was trained
from datetime import datetime

# statsmodels.tsa.arima.model.ARIMA: The ARIMA implementation
# 'tsa' = Time Series Analysis
from statsmodels.tsa.arima.model import ARIMA

# warnings: To suppress convergence warnings from ARIMA
import warnings
warnings.filterwarnings('ignore')  # ARIMA can be noisy


# =============================================================================
# CONFIGURATION
# =============================================================================

# Path to the input data (created by data_pipeline.py)
DATA_PATH = "../data/clean_data.csv"

# Where to save the trained model
MODEL_DIR = "../saved_models"
MODEL_PATH = os.path.join(MODEL_DIR, "arima_model.pkl")

# ARIMA hyperparameters
# (5, 1, 0) is a good starting point for hourly/minute data
ARIMA_ORDER = (5, 1, 0)

# Maximum training samples (for speed during development)
# ARIMA training is O(n³), so 20,000 samples is plenty.
MAX_TRAINING_SAMPLES = 20000


# =============================================================================
# EVALUATION METRICS: How we measure model quality
# =============================================================================

def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate Root Mean Square Error (RMSE).
    
    WHAT IS RMSE?
    -------------
    RMSE measures how far off our predictions are, on average.
    It's in the same units as the data (e.g., "requests per minute").
    
    FORMULA:
    --------
    RMSE = √(mean((actual - predicted)²))
    
    STEPS:
    ------
    1. Calculate the error for each point: (actual - predicted)
    2. Square each error: error²
    3. Take the mean of squared errors: mean(error²)
    4. Take the square root: √(mean)
    
    WHY SQUARE AND THEN SQRT?
    -------------------------
    - Squaring penalizes large errors more (good for avoiding disasters)
    - Taking sqrt brings it back to original units (interpretable)
    
    EXAMPLE:
    --------
    actual    = [100, 200, 150]
    predicted = [110, 190, 160]
    errors    = [-10, 10, -10]
    squared   = [100, 100, 100]
    mean      = 100
    rmse      = √100 = 10
    
    Interpretation: "On average, we're off by 10 requests per minute."
    
    PARAMETERS:
    -----------
    actual : np.ndarray
        The true values.
    predicted : np.ndarray
        Our model's predictions.
    
    RETURNS:
    --------
    float : The RMSE value (lower is better).
    """
    
    # Step 1-2: Calculate squared errors
    squared_errors = (actual - predicted) ** 2
    
    # Step 3: Mean of squared errors
    mean_squared_error = np.mean(squared_errors)
    
    # Step 4: Square root
    rmse = np.sqrt(mean_squared_error)
    
    return rmse


def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate Mean Absolute Error (MAE).
    
    WHAT IS MAE?
    ------------
    MAE is simpler than RMSE: just average the absolute errors.
    It doesn't penalize large errors as much as RMSE.
    
    FORMULA:
    --------
    MAE = mean(|actual - predicted|)
    
    EXAMPLE:
    --------
    actual    = [100, 200, 150]
    predicted = [110, 190, 160]
    errors    = [10, 10, 10]  (absolute values)
    mae       = mean([10, 10, 10]) = 10
    
    Interpretation: "On average, we're off by 10 requests per minute."
    
    PARAMETERS:
    -----------
    actual : np.ndarray
        The true values.
    predicted : np.ndarray
        Our model's predictions.
    
    RETURNS:
    --------
    float : The MAE value (lower is better).
    """
    
    # Absolute errors: |actual - predicted|
    absolute_errors = np.abs(actual - predicted)
    
    # Mean of absolute errors
    mae = np.mean(absolute_errors)
    
    return mae


def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate Mean Absolute Percentage Error (MAPE).
    
    WHAT IS MAPE?
    -------------
    MAPE expresses error as a percentage.
    This is useful when comparing across datasets of different scales.
    
    FORMULA:
    --------
    MAPE = mean(|actual - predicted| / |actual|) * 100
    
    EXAMPLE:
    --------
    actual    = [100, 200, 150]
    predicted = [110, 190, 160]
    pct_error = [10/100, 10/200, 10/150] = [0.10, 0.05, 0.067]
    mape      = mean([0.10, 0.05, 0.067]) * 100 = 7.2%
    
    Interpretation: "On average, we're off by 7.2% of the actual value."
    
    CAVEAT:
    -------
    MAPE can explode if actual values are near zero!
    We handle this by adding a small epsilon.
    
    PARAMETERS:
    -----------
    actual : np.ndarray
        The true values.
    predicted : np.ndarray
        Our model's predictions.
    
    RETURNS:
    --------
    float : The MAPE value as a percentage (lower is better).
    """
    
    # Avoid division by zero: add tiny value
    epsilon = 1e-10
    safe_actual = np.abs(actual) + epsilon
    
    # Calculate percentage errors
    percentage_errors = np.abs(actual - predicted) / safe_actual
    
    # Mean, then convert to percentage
    mape = np.mean(percentage_errors) * 100
    
    return mape


# =============================================================================
# ARIMA TRAINER CLASS
# =============================================================================

class ARIMATrainer:
    """
    A class to train and evaluate ARIMA models.
    
    WHY USE A CLASS?
    ----------------
    - Encapsulates all training logic in one place
    - Keeps state (trained model, metrics) between method calls
    - Makes code reusable and testable
    
    ATTRIBUTES:
    -----------
    order : tuple
        The (p, d, q) parameters for ARIMA.
    model : statsmodels.ARIMAResults
        The trained model (None until train() is called).
    metrics : dict
        Evaluation metrics (RMSE, MAE, MAPE).
    trained_at : datetime
        When the model was trained.
    
    METHODS:
    --------
    load_data() : Load and preprocess the training data.
    train(data) : Train the ARIMA model.
    evaluate(actual) : Calculate performance metrics.
    save() : Save the model to disk.
    """
    
    def __init__(self, order: tuple = ARIMA_ORDER):
        """
        Initialize the trainer.
        
        PARAMETERS:
        -----------
        order : tuple
            ARIMA parameters (p, d, q). Default is (5, 1, 0).
        """
        
        self.order = order           # ARIMA parameters
        self.model = None            # Will hold the trained model
        self.metrics = {}            # Will store RMSE, MAE, MAPE
        self.trained_at = None       # Timestamp of training
        
        print(f"📦 ARIMATrainer initialized with order={order}")
    
    
    def load_data(self) -> np.ndarray:
        """
        Load training data from CSV.
        
        RETURNS:
        --------
        np.ndarray : The 'requests' column as a 1D array.
        
        RAISES:
        -------
        FileNotFoundError : If the data file doesn't exist.
        """
        
        print(f"\n📥 Loading data from {DATA_PATH}...")
        
        # Check if file exists
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(
                f"Data file not found: {DATA_PATH}\n"
                f"Please run 'python src/data_pipeline.py' first."
            )
        
        # Load CSV into DataFrame
        df = pd.read_csv(DATA_PATH)
        
        # Parse timestamp column
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by time (important for time-series!)
        df = df.sort_values('timestamp')
        
        print(f"   Loaded {len(df)} rows")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Downsample if too large (for training speed)
        if len(df) > MAX_TRAINING_SAMPLES:
            print(f"   ⚠️ Dataset large. Sampling {MAX_TRAINING_SAMPLES} points...")
            # Take every Nth row to get MAX_TRAINING_SAMPLES
            step = len(df) // MAX_TRAINING_SAMPLES
            df = df.iloc[::step].head(MAX_TRAINING_SAMPLES)
        
        # Extract 'requests' column as numpy array
        data = df['requests'].values
        
        print(f"   Training data shape: {data.shape}")
        print(f"   Mean requests: {np.mean(data):.2f}")
        print(f"   Std requests: {np.std(data):.2f}")
        
        return data
    
    
    def train(self, data: np.ndarray):
        """
        Train the ARIMA model.
        
        PARAMETERS:
        -----------
        data : np.ndarray
            The time-series data to train on.
        
        RETURNS:
        --------
        self : For method chaining.
        
        HOW IT WORKS:
        -------------
        1. Create an ARIMA model with the specified order.
        2. Fit the model to the data (find optimal parameters).
        3. Store the fitted model for later use.
        """
        
        print(f"\n🧠 Training ARIMA{self.order} model...")
        print(f"   This may take a moment...")
        
        start_time = time.time()
        
        # Create and fit the model
        # ARIMA(data, order) creates the model structure
        # .fit() actually trains it
        arima = ARIMA(data, order=self.order)
        self.model = arima.fit()
        
        # Record training time
        duration = time.time() - start_time
        self.trained_at = datetime.now()
        
        print(f"   ✅ Training completed in {duration:.2f} seconds")
        print(f"   Trained at: {self.trained_at}")
        
        return self
    
    
    def evaluate(self, data: np.ndarray):
        """
        Evaluate the trained model.
        
        PARAMETERS:
        -----------
        data : np.ndarray
            The same data used for training (in-sample evaluation).
        
        RETURNS:
        --------
        dict : Metrics dictionary with RMSE, MAE, MAPE.
        
        NOTE:
        -----
        This is "in-sample" evaluation (predicting training data).
        For a real competition, you'd use a separate test set.
        We're simplifying for this demo.
        """
        
        print(f"\n📊 Evaluating model performance...")
        
        if self.model is None:
            raise ValueError("Model not trained yet! Call train() first.")
        
        # Get in-sample predictions
        # predict(start, end) predicts for those indices
        predictions = self.model.predict(start=0, end=len(data)-1)
        
        # Calculate metrics
        rmse = calculate_rmse(data, predictions)
        mae = calculate_mae(data, predictions)
        mape = calculate_mape(data, predictions)
        
        # Store in dict
        self.metrics = {
            'rmse': rmse,
            'mae': mae,
            'mape': mape
        }
        
        # Print results
        print(f"   RMSE: {rmse:.4f} (requests/min)")
        print(f"   MAE:  {mae:.4f} (requests/min)")
        print(f"   MAPE: {mape:.2f}%")
        
        return self.metrics
    
    
    def save(self):
        """
        Save the trained model to disk.
        
        WHY SAVE?
        ---------
        Training takes time. We don't want to re-train every time the API starts.
        Instead, we train once, save to disk, and load when needed.
        
        FORMAT:
        -------
        We use Python's 'pickle' module to serialize the model.
        The file extension '.pkl' is convention for pickle files.
        """
        
        print(f"\n💾 Saving model to {MODEL_PATH}...")
        
        if self.model is None:
            raise ValueError("Model not trained yet! Call train() first.")
        
        # Create directory if it doesn't exist
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
            print(f"   Created directory: {MODEL_DIR}")
        
        # Save using pickle
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Verify file was created
        file_size = os.path.getsize(MODEL_PATH) / 1024  # KB
        print(f"   ✅ Model saved ({file_size:.1f} KB)")
        
        # Also save metrics for dashboard to display
        metrics_path = os.path.join(MODEL_DIR, "metrics.pkl")
        with open(metrics_path, 'wb') as f:
            pickle.dump(self.metrics, f)
        print(f"   ✅ Metrics saved to {metrics_path}")


# =============================================================================
# MAIN TRAINING PIPELINE
# =============================================================================

def run_training_pipeline():
    """
    Execute the full training pipeline.
    
    This is the main function that orchestrates:
    1. Loading data
    2. Training the model
    3. Evaluating performance
    4. Saving artifacts
    """
    
    print("="*60)
    print("  MODEL TRAINING PIPELINE - M2 (Modeler)")
    print("="*60)
    
    try:
        # Initialize trainer
        trainer = ARIMATrainer()
        
        # Load data (from M1's output)
        data = trainer.load_data()
        
        # Train the model
        trainer.train(data)
        
        # Evaluate performance
        trainer.evaluate(data)
        
        # Save to disk
        trainer.save()
        
        # Success!
        print("\n" + "="*60)
        print("  ✅ TRAINING PIPELINE COMPLETE")
        print("="*60)
        print(f"\nModel saved to: {MODEL_PATH}")
        print("The Backend API can now load and use this model.")
        print("\nNext steps:")
        print("  1. Start the API: uvicorn app:app --reload")
        print("  2. Open Dashboard: streamlit run dashboard/main.py")
        
    except Exception as e:
        print(f"\n❌ TRAINING FAILED: {e}")
        raise


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run_training_pipeline()
