import pandas as pd
import re
import os
from datetime import datetime

# Define file paths
input_train = r'c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\DATA\train.txt'
input_test = r'c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\DATA\test.txt'
output_dir = r'c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\processed_data'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Regex for parsing Common Log Format (extended to capture what we need)
# Example: 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /history/apollo/ HTTP/1.0" 200 6245
# Regex for parsing Common Log Format (extended to capture what we need)
# Example: 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /history/apollo/ HTTP/1.0" 200 6245
log_pattern = re.compile(r'(?P<host>\S+) - - \[(?P<timestamp>.*?)\] "(?P<request>.*?)" (?P<status>\d{3}) (?P<bytes>\S+)')

def parse_line(line):
    match = log_pattern.match(line)
    if match:
        data = match.groupdict()
        # Handle bytes being '-' which means 0
        if data['bytes'] == '-':
            data['bytes'] = 0
        else:
            try:
                data['bytes'] = int(data['bytes'])
            except ValueError:
                data['bytes'] = 0
        
        # Parse Request (Method, Path, Protocol)
        # Some requests might be malformed or simple like "GET /"
        request_parts = data['request'].split()
        if len(request_parts) >= 2:
            data['method'] = request_parts[0]
            data['path'] = request_parts[1]
            data['protocol'] = request_parts[2] if len(request_parts) > 2 else ''
        else:
            data['method'] = ''
            data['path'] = data['request']
            data['protocol'] = ''
            
        return data
    return None

def process_file(filepath, chunk_size=100000):
    print(f"Processing {filepath}...")
    records = []
    
    # We will read line by line to avoid memory issues with huge files
    with open(filepath, 'r', encoding='latin-1') as f:
        for i, line in enumerate(f):
            parsed = parse_line(line)
            if parsed:
                records.append(parsed)
            
            if i % 500000 == 0 and i > 0:
                print(f"  Parsed {i} lines...")

    df = pd.DataFrame(records)
    print(f"  Finished parsing. Total records: {len(df)}")
    
    # Convert timestamp to datetime
    print("  Converting timestamps...")
    # Format: 01/Jul/1995:00:00:01 -0400
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d/%b/%Y:%H:%M:%S %z', errors='coerce')
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['timestamp'])
    
    return df

# Process both files
df_train = process_file(input_train)
df_test = process_file(input_test)

# Combine datasets
print("Combining datasets...")
df_full = pd.concat([df_train, df_test])
df_full = df_full.sort_values('timestamp')

# Save Full Cleaned Dataset (with IP and Path)
print("Saving full cleaned dataset (nasa_logs_clean.csv)...")
# Select relevant columns
cols = ['timestamp', 'host', 'method', 'path', 'status', 'bytes']
df_full[cols].to_csv(os.path.join(output_dir, 'nasa_logs_clean.csv'), index=False)
print("  Saved full logs.")

# Set timestamp as index for resampling
df_full.set_index('timestamp', inplace=True)

# Pre-calculate status categories for aggregation
print("Encoding status codes...")
df_full['status'] = df_full['status'].astype(int)
df_full['status_2xx'] = ((df_full['status'] >= 200) & (df_full['status'] < 300)).astype(int)
df_full['status_3xx'] = ((df_full['status'] >= 300) & (df_full['status'] < 400)).astype(int)
df_full['status_4xx'] = ((df_full['status'] >= 400) & (df_full['status'] < 500)).astype(int)
df_full['status_5xx'] = ((df_full['status'] >= 500) & (df_full['status'] < 600)).astype(int)

# Define Resampling Function
def resample_and_save(df, interval, filename):
    print(f"Resampling to {interval}...")
    # Resample counts (requests) and sum (bytes)
    resampled = df.resample(interval).agg({
        'path': 'count', # Total requests
        'bytes': 'sum',
        'status_2xx': 'sum',
        'status_3xx': 'sum',
        'status_4xx': 'sum',
        'status_5xx': 'sum'
    }).rename(columns={'path': 'requests_count', 'bytes': 'bytes_sum'})
    
    output_path = os.path.join(output_dir, filename)
    resampled.to_csv(output_path)
    print(f"  Saved to {output_path}")

# Resample to 1min, 5min, 15min
resample_and_save(df_full, '1min', 'nasa_traffic_1m.csv')
resample_and_save(df_full, '5min', 'nasa_traffic_5m.csv')
resample_and_save(df_full, '15min', 'nasa_traffic_15m.csv')

print("Data Engineering Complete.")
