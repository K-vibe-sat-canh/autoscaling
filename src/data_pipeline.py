"""
================================================================================
FILE: src/data_pipeline.py
ROLE: M1 (Data Cleaning / Data Engineer)
PURPOSE: Generate synthetic HTTP access log data for training and simulation.
================================================================================

This script simulates what M1 (Data Cleaning member) would do:
1. Parse raw HTTP logs (in our case, we generate synthetic data)
2. Extract fields: timestamp, requests count, bytes transferred
3. Handle the "Storm" period (01/08 - 03/08) where data is missing
4. Output a clean CSV file for model training

WHY SYNTHETIC DATA?
-------------------
The competition provides raw ASCII logs from 1995. Parsing those requires
regex and careful timestamp handling. For this demo, we generate data that
MIMICS the statistical properties of real web traffic:
- Higher load during daytime (9AM - 9PM)
- Lower load at night
- Random spikes (simulating viral content)
- A "Storm" gap (missing data period)

USAGE:
------
    cd uibackend
    python src/data_pipeline.py

OUTPUT:
-------
    data/clean_data.csv
    
    Columns:
    - timestamp: DateTime in ISO format (YYYY-MM-DD HH:MM:SS)
    - requests: Number of HTTP requests in that minute
    - bytes: Total bytes transferred in that minute

================================================================================
"""

# =============================================================================
# IMPORTS - Libraries we need
# =============================================================================

# 'pandas' is THE library for data manipulation in Python.
# Think of it as "Excel for Python" - it handles tables (DataFrames).
import pandas as pd

# 'numpy' is for numerical operations (math, random numbers, arrays).
# We use it here to generate realistic traffic patterns.
import numpy as np

# 'datetime' helps us work with dates and times.
# 'timedelta' lets us add/subtract time (e.g., "1 minute later").
from datetime import datetime, timedelta

# 'random' is Python's built-in random number generator.
# We use it for adding "noise" to our synthetic data.
import random

# 'os' provides functions to interact with the operating system.
# We use it to create directories and check if files exist.
import os


# =============================================================================
# CONFIGURATION - Parameters you can tweak
# =============================================================================

# Where to save the output CSV file.
# "../data" means "go up one folder, then into 'data' folder".
OUTPUT_DIR = "../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "clean_data.csv")

# How many days of data to generate?
# The competition uses July + August 1995 = 62 days.
DAYS_TO_GENERATE = 60

# Start date matches the competition description.
START_DATE = datetime(1995, 7, 1, 0, 0, 0)

# The "Storm" period: Server was down, no logs recorded.
# From 01/08/1995 14:52:01 to 03/08/1995 04:36:13
STORM_START = datetime(1995, 8, 1, 14, 52, 1)
STORM_END = datetime(1995, 8, 3, 4, 36, 13)


# =============================================================================
# HELPER FUNCTION: Generate realistic traffic for one minute
# =============================================================================

def generate_minute_traffic(current_time: datetime) -> tuple:
    """
    Generates synthetic HTTP traffic for a single minute.
    
    PARAMETERS:
    -----------
    current_time : datetime
        The timestamp we're generating traffic for.
    
    RETURNS:
    --------
    tuple : (requests_count, bytes_count)
        - requests_count: How many HTTP requests happened this minute.
        - bytes_count: How many bytes were transferred.
    
    HOW IT WORKS:
    -------------
    1. BASE LOAD: We start with a "base" of 500-1500 requests per minute.
    
    2. TIME-OF-DAY FACTOR: Traffic is higher during the day.
       - We use a sine wave that peaks at 2PM (14:00).
       - Night time (2AM) has the lowest traffic.
       - Formula: sin((hour - 6) * π / 12) gives us a wave from -1 to +1.
       - We shift it up so it's always positive: (sin(...) + 1.2)
    
    3. RANDOM NOISE: Real traffic isn't perfectly smooth.
       - We add random variation of ±200 requests.
    
    4. SPIKES: Sometimes there's a sudden surge (viral content, etc.)
       - 0.1% chance per minute of a 3x traffic spike.
    
    5. BYTES: Each request transfers some data.
       - On average, 500-2000 bytes per request (like HTML pages).
    
    EXAMPLE:
    --------
    >>> generate_minute_traffic(datetime(1995, 7, 15, 14, 30, 0))
    (1523, 1842967)  # 1523 requests, ~1.8MB transferred
    """
    
    # === STEP 1: BASE LOAD ===
    # A typical minute has 500-1500 requests.
    base_requests = random.randint(500, 1500)
    
    # === STEP 2: TIME-OF-DAY FACTOR ===
    # Extract the hour (0-23) from the timestamp.
    hour = current_time.hour
    
    # Apply a sine wave pattern:
    # - Peak at hour=14 (2PM), trough at hour=2 (2AM)
    # - np.sin() takes radians, so we convert: (hour - 6) * π / 12
    # - Adding 1.2 shifts the wave so it's always positive (range: 0.2 to 2.2)
    daily_factor = np.sin((hour - 6) * np.pi / 12) + 1.2
    
    # Multiply base by the daily factor
    adjusted_requests = base_requests * daily_factor
    
    # === STEP 3: RANDOM NOISE ===
    noise = random.randint(-200, 200)
    adjusted_requests += noise
    
    # === STEP 4: RANDOM SPIKES ===
    # 0.001 = 0.1% chance of a traffic spike
    if random.random() < 0.001:
        adjusted_requests *= 3.0  # Triple the traffic!
    
    # Ensure we never have negative requests
    requests_count = max(0, int(adjusted_requests))
    
    # === STEP 5: CALCULATE BYTES ===
    # Each request transfers 500-2000 bytes on average
    bytes_per_request = random.randint(500, 2000)
    bytes_count = requests_count * bytes_per_request
    
    return requests_count, bytes_count


# =============================================================================
# MAIN FUNCTION: Generate the entire dataset
# =============================================================================

def generate_full_dataset():
    """
    Generates the complete synthetic dataset.
    
    This function:
    1. Loops through every minute for DAYS_TO_GENERATE days.
    2. Generates traffic for each minute using generate_minute_traffic().
    3. Skips the "Storm" period (no data during server outage).
    4. Saves everything to a CSV file.
    
    NO PARAMETERS (uses global config).
    
    RETURNS:
    --------
    pd.DataFrame : The complete dataset with columns:
        - timestamp
        - requests
        - bytes
    """
    
    print("="*60)
    print("  DATA PIPELINE - M1 (Data Cleaning)")
    print("="*60)
    print(f"\n📅 Generating {DAYS_TO_GENERATE} days of traffic data...")
    print(f"   Start: {START_DATE}")
    print(f"   Storm Period: {STORM_START} to {STORM_END}")
    print()
    
    # === PREPARE STORAGE ===
    # We'll collect data in lists (faster than appending to DataFrame).
    timestamps = []
    requests_list = []
    bytes_list = []
    
    # === LOOP THROUGH TIME ===
    current_time = START_DATE
    end_time = START_DATE + timedelta(days=DAYS_TO_GENERATE)
    
    # Track progress
    total_minutes = DAYS_TO_GENERATE * 24 * 60
    processed = 0
    
    while current_time < end_time:
        
        # === CHECK FOR STORM PERIOD ===
        # If we're in the storm window, skip this minute (no data).
        if STORM_START <= current_time <= STORM_END:
            current_time += timedelta(minutes=1)
            processed += 1
            continue
        
        # === GENERATE TRAFFIC ===
        reqs, bytes_val = generate_minute_traffic(current_time)
        
        # === STORE DATA ===
        timestamps.append(current_time)
        requests_list.append(reqs)
        bytes_list.append(bytes_val)
        
        # === ADVANCE TIME ===
        current_time += timedelta(minutes=1)
        processed += 1
        
        # === PROGRESS INDICATOR ===
        # Print every 10,000 minutes to show we're working
        if processed % 10000 == 0:
            print(f"   Processed {processed}/{total_minutes} minutes...")
    
    # === CREATE DATAFRAME ===
    print("\n📊 Creating DataFrame...")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "requests": requests_list,
        "bytes": bytes_list
    })
    
    print(f"   Total rows: {len(df)}")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df


# =============================================================================
# SAVE FUNCTION: Export to CSV
# =============================================================================

def save_to_csv(df: pd.DataFrame):
    """
    Saves the DataFrame to a CSV file.
    
    PARAMETERS:
    -----------
    df : pd.DataFrame
        The dataset to save.
    
    WHY CSV?
    --------
    - Universal format (Excel, Python, R all read it).
    - Human-readable (you can open it in Notepad).
    - Required by the competition ("Data sạch CSV").
    """
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created directory: {OUTPUT_DIR}")
    
    # Save to CSV
    # index=False means don't save the row numbers (0, 1, 2, ...)
    df.to_csv(OUTPUT_FILE, index=False)
    
    # Get file size for confirmation
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # Convert to MB
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print(f"   File size: {file_size:.2f} MB")


# =============================================================================
# ENTRY POINT: Run when script is executed directly
# =============================================================================

if __name__ == "__main__":
    """
    This block runs when you execute: python data_pipeline.py
    
    It does NOT run if you import this file from another script.
    Example:
        # This runs __main__:
        python data_pipeline.py
        
        # This does NOT run __main__:
        from data_pipeline import generate_full_dataset
    """
    
    # Generate the dataset
    df = generate_full_dataset()
    
    # Save to CSV
    save_to_csv(df)
    
    # Success message
    print("\n" + "="*60)
    print("  ✅ DATA PIPELINE COMPLETE")
    print("="*60)
    print("\nNext step: Train models using this data.")
    print("Run: python src/model_trainer.py")
