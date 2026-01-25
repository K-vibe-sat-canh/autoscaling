"""
Missing Data Handler for NASA Traffic Time Series
Provides multiple strategies for handling the 01/08-03/08 outage period.

Usage:
    from handle_missing_data import MissingDataHandler
    handler = MissingDataHandler('processed_data/nasa_traffic_1m.csv')
    
    # For Prophet/ARIMA (accepts NaN)
    df_prophet = handler.keep_nan()
    
    # For LSTM/XGBoost (needs complete data)
    df_lstm = handler.seasonal_interpolation()
    
    # Simple approach
    df_simple = handler.drop_outage()
"""

import pandas as pd
import numpy as np
from typing import Literal


class MissingDataHandler:
    """Handle missing data in NASA traffic time series."""
    
    def __init__(self, filepath: str):
        """Load time series data."""
        self.df = pd.read_csv(filepath, parse_dates=['timestamp'])
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        
        # Identify metric columns (exclude timestamp and flags)
        self.metric_cols = ['request_count', 'total_bytes', 
                          'status_2xx', 'status_3xx', 'status_4xx', 'status_5xx']
        
        print(f"Loaded {len(self.df)} rows")
        print(f"Outage rows: {self.df['is_outage'].sum()}")
        print(f"Date range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
    
    def keep_nan(self) -> pd.DataFrame:
        """
        Strategy 1: Keep NaN values as-is.
        Best for: Prophet, ARIMA (models that handle missing data natively)
        """
        return self.df.copy()
    
    def drop_outage(self) -> pd.DataFrame:
        """
        Strategy 2: Drop all rows during outage period.
        Best for: Simple analysis, when time continuity is not critical
        Warning: Creates gap in time series!
        """
        df_clean = self.df[self.df['is_outage'] == 0].copy()
        df_clean = df_clean.reset_index(drop=True)
        print(f"Dropped {len(self.df) - len(df_clean)} outage rows")
        return df_clean
    
    def fill_zero(self) -> pd.DataFrame:
        """
        Strategy 3: Fill NaN with 0.
        Warning: NOT recommended - confuses 'server down' with 'no traffic'
        Only use if you also use is_outage as a feature!
        """
        df_filled = self.df.copy()
        df_filled[self.metric_cols] = df_filled[self.metric_cols].fillna(0)
        return df_filled
    
    def seasonal_interpolation(self) -> pd.DataFrame:
        """
        Strategy 4: Fill NaN using seasonal pattern (same hour/minute/dayofweek).
        Best for: LSTM, XGBoost, models requiring complete data
        Preserves daily/weekly patterns.
        """
        df_filled = self.df.copy()
        
        # Extract time components
        df_filled['hour'] = df_filled['timestamp'].dt.hour
        df_filled['minute'] = df_filled['timestamp'].dt.minute
        df_filled['dayofweek'] = df_filled['timestamp'].dt.dayofweek
        
        # Calculate patterns from non-outage data
        non_outage = df_filled[df_filled['is_outage'] == 0]
        
        for col in self.metric_cols:
            # Group by (hour, minute, dayofweek) and get mean
            pattern = non_outage.groupby(['hour', 'minute', 'dayofweek'])[col].mean()
            
            # Fill missing values
            def fill_from_pattern(row):
                if pd.isna(row[col]):
                    key = (row['hour'], row['minute'], row['dayofweek'])
                    if key in pattern.index:
                        return pattern[key]
                    # Fallback: use hourly mean if exact match not found
                    hourly_mean = non_outage[non_outage['hour'] == row['hour']][col].mean()
                    return hourly_mean if not pd.isna(hourly_mean) else 0
                return row[col]
            
            df_filled[col] = df_filled.apply(fill_from_pattern, axis=1)
        
        # Clean up helper columns
        df_filled = df_filled.drop(columns=['hour', 'minute', 'dayofweek'])
        
        print(f"Filled {self.df['is_outage'].sum()} outage rows with seasonal patterns")
        return df_filled
    
    def linear_interpolation(self) -> pd.DataFrame:
        """
        Strategy 5: Linear interpolation.
        Warning: Not ideal for 37-hour gap - will smooth out patterns!
        """
        df_filled = self.df.copy()
        df_filled[self.metric_cols] = df_filled[self.metric_cols].interpolate(method='linear')
        return df_filled
    
    def get_train_test_split(self, df: pd.DataFrame = None) -> tuple:
        """
        Split data according to competition rules:
        - Train: July + first 22 days of August
        - Test: Remaining August days (23-31)
        """
        if df is None:
            df = self.df
        
        # Train: up to Aug 22 23:59:59
        train_end = pd.Timestamp("1995-08-22 23:59:59", tz=df['timestamp'].dt.tz)
        
        train = df[df['timestamp'] <= train_end].copy()
        test = df[df['timestamp'] > train_end].copy()
        
        print(f"Train: {len(train)} rows ({train['timestamp'].min()} to {train['timestamp'].max()})")
        print(f"Test: {len(test)} rows ({test['timestamp'].min()} to {test['timestamp'].max()})")
        
        return train, test


def demo():
    """Demonstrate different strategies."""
    print("="*60)
    print("MISSING DATA HANDLING DEMO")
    print("="*60)
    
    # Load 1-minute data
    handler = MissingDataHandler('processed_data/nasa_traffic_1m.csv')
    
    print("\n--- Strategy Comparison ---")
    
    # Compare means
    strategies = {
        'Original (NaN)': handler.keep_nan(),
        'Drop Outage': handler.drop_outage(),
        'Seasonal Fill': handler.seasonal_interpolation(),
    }
    
    print("\nMean request_count comparison:")
    for name, df in strategies.items():
        mean_val = df['request_count'].mean()
        nan_count = df['request_count'].isna().sum()
        print(f"  {name}: mean={mean_val:.2f}, NaN={nan_count}")
    
    # Show train/test split
    print("\n--- Train/Test Split ---")
    df_clean = handler.drop_outage()
    train, test = handler.get_train_test_split(df_clean)


if __name__ == '__main__':
    demo()
