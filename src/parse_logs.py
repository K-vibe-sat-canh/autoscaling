import re
import pandas as pd
from datetime import datetime
import glob
import os

# Define paths
DATA_DIR = r"c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\DATA"
OUTPUT_DIR = r"c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\processed_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nasa_traffic_1m.csv")

# Regex Pattern
# IP - - [Timestamp] "Method URL Protocol" Status Size
LOG_PATTERN = re.compile(r'^(\S+) \S+ \S+ \[(.*?)\] "(?:GET|POST|HEAD|PUT|DELETE) (\S+) .*?" \d+ (\d+|-)')

def parse_log_line(line):
    match = LOG_PATTERN.match(line)
    if match:
        # timestamp = match.group(2)
        # size_str = match.group(4)
        return match.group(2), match.group(4)
    return None, None

def parse_logs(file_paths):
    data = []
    print(f"Parsing files: {file_paths}")
    
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                ts_str, size_str = parse_log_line(line)
                if ts_str:
                    # Handle size '-'
                    size = 0 if size_str == '-' else int(size_str)
                    data.append((ts_str, size))
    
    return data

def main():
    # Find log files 
    # specific to the user's files: test.txt and train.txt seem to be the ones
    log_files = [
        os.path.join(DATA_DIR, "train.txt"), # Usually larger, start with this or both
        os.path.join(DATA_DIR, "test.txt")
    ]
    
    # Filter only existing files
    log_files = [f for f in log_files if os.path.exists(f)]
    
    if not log_files:
        print("No log files found in DATA directory.")
        return

    # Parse
    raw_data = parse_logs(log_files)
    print(f"Parsed {len(raw_data)} records.")

    # Create DataFrame
    df = pd.DataFrame(raw_data, columns=['timestamp_str', 'bytes'])

    # Convert timestamp
    # Format: 01/Jul/1995:00:00:01 -0400
    print("Converting timestamps...")
    df['timestamp'] = pd.to_datetime(df['timestamp_str'], format='%d/%b/%Y:%H:%M:%S %z', errors='coerce')
    
    # Drop invalid dates if any
    df = df.dropna(subset=['timestamp'])

    # Set index
    df.set_index('timestamp', inplace=True)
    
    # Sort
    df.sort_index(inplace=True)

    # Convert bytes to numeric just in case
    df['bytes'] = pd.to_numeric(df['bytes'])

    # Aggregate to 1 minute
    print("Resampling to 1 minute...")
    df_1m = df.resample('1min').agg({
        'bytes': ['count', 'sum']
    })
    
    # Flatten columns
    df_1m.columns = ['request_count', 'total_bytes']
    
    # Fill NaN with 0 (no traffic in that minute)
    df_1m = df_1m.fillna(0)

    # Save
    print(f"Saving to {OUTPUT_FILE}...")
    df_1m.to_csv(OUTPUT_FILE)
    print("Done.")

if __name__ == "__main__":
    main()
