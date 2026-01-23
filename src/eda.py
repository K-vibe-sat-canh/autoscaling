import pandas as pd
import os

# Load Data
data_path = r'c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS\processed_data\nasa_traffic_5m.csv'
df = pd.read_csv(data_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Generate Summary Statistics
print("Summary Statistics:")
print(df.describe())

# Check for Data Gap
# We expect a gap around Aug 1-3 from 14:52:01 01/08/1995 to 04:36:13 03/08/1995
print("\nChecking for missing timestamps (Gap > 10 mins)...")
df['time_diff'] = df.index.to_series().diff().dt.total_seconds() / 60
gaps = df[df['time_diff'] > 10]
print("Found gaps:")
print(gaps[['time_diff']])

print("\nVerifying specific known gap window:")
gap_start = pd.Timestamp('1995-08-01 14:50:00', tz='UTC-04:00')
gap_end = pd.Timestamp('1995-08-03 04:40:00', tz='UTC-04:00')

# Filter data around the gap
around_gap = df[(df.index >= gap_start) & (df.index <= gap_end)]
if around_gap.empty:
    print("  CONFIRMED: No data points found in the known gap window.")
else:
    print("  WARNING: Data points found in the gap window!")
    print(around_gap)

print("EDA Text Analysis Complete.")
