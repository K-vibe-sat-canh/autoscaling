"""
NASA Traffic Data - Exploratory Data Analysis (EDA)
====================================================
Phan tich du lieu traffic NASA de chuan bi cho bai toan Autoscaling.

Bao gom:
1. Thong ke tong quan
2. Missing data analysis (Outage period)
3. Time series patterns (Daily, Weekly)
4. Distribution analysis
5. Anomaly/Spike detection
6. Train/Test split visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10

# ============================================================
# 1. LOAD DATA
# ============================================================
print("="*60)
print("1. LOADING DATA")
print("="*60)

DATA_DIR = 'processed_data'

# Load different resolutions
df_1m = pd.read_csv(f'{DATA_DIR}/nasa_traffic_1m.csv', parse_dates=['timestamp'])
df_5m = pd.read_csv(f'{DATA_DIR}/nasa_traffic_5m.csv', parse_dates=['timestamp'])
df_15m = pd.read_csv(f'{DATA_DIR}/nasa_traffic_15m.csv', parse_dates=['timestamp'])

print(f"1-minute data: {len(df_1m):,} rows")
print(f"5-minute data: {len(df_5m):,} rows")
print(f"15-minute data: {len(df_15m):,} rows")

# Use 5-minute data for main analysis (balanced granularity)
df = df_5m.copy()
df = df.sort_values('timestamp').reset_index(drop=True)

print(f"\nDate range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Duration: {(df['timestamp'].max() - df['timestamp'].min()).days} days")

# ============================================================
# 2. BASIC STATISTICS
# ============================================================
print("\n" + "="*60)
print("2. BASIC STATISTICS")
print("="*60)

# Exclude outage for meaningful stats
df_valid = df[df['is_outage'] == 0].copy()

print("\n--- Request Count Statistics (non-outage) ---")
print(df_valid['request_count'].describe())

print("\n--- Total Bytes Statistics (non-outage) ---")
print(df_valid['total_bytes'].describe())

print("\n--- Status Code Distribution ---")
status_cols = ['status_2xx', 'status_3xx', 'status_4xx', 'status_5xx']
status_totals = df_valid[status_cols].sum()
status_pct = (status_totals / status_totals.sum() * 100).round(2)
print(pd.DataFrame({'Count': status_totals, 'Percentage': status_pct}))

# ============================================================
# 3. MISSING DATA ANALYSIS (OUTAGE)
# ============================================================
print("\n" + "="*60)
print("3. MISSING DATA / OUTAGE ANALYSIS")
print("="*60)

outage_rows = df[df['is_outage'] == 1]
print(f"Outage rows: {len(outage_rows)} ({len(outage_rows)/len(df)*100:.2f}%)")
print(f"Outage start: {outage_rows['timestamp'].min()}")
print(f"Outage end: {outage_rows['timestamp'].max()}")
print(f"Outage duration: {(outage_rows['timestamp'].max() - outage_rows['timestamp'].min())}")

# Check NaN values
print("\n--- NaN Values per Column ---")
nan_counts = df.isna().sum()
print(nan_counts[nan_counts > 0])

# ============================================================
# 4. TIME SERIES VISUALIZATION
# ============================================================
print("\n" + "="*60)
print("4. CREATING VISUALIZATIONS")
print("="*60)

# Create output directory
os.makedirs('outputs/eda', exist_ok=True)

# 4.1 Overall Traffic Pattern
fig, axes = plt.subplots(2, 1, figsize=(16, 10))

# Request count
ax1 = axes[0]
ax1.plot(df['timestamp'], df['request_count'], linewidth=0.5, alpha=0.8)
ax1.axvspan(outage_rows['timestamp'].min(), outage_rows['timestamp'].max(), 
            alpha=0.3, color='red', label='Outage Period')
ax1.set_ylabel('Request Count (per 5min)')
ax1.set_title('NASA HTTP Traffic - Request Count Over Time')
ax1.legend()
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

# Total bytes
ax2 = axes[1]
ax2.plot(df['timestamp'], df['total_bytes']/1e6, linewidth=0.5, alpha=0.8, color='green')
ax2.axvspan(outage_rows['timestamp'].min(), outage_rows['timestamp'].max(), 
            alpha=0.3, color='red', label='Outage Period')
ax2.set_ylabel('Total Bytes (MB per 5min)')
ax2.set_xlabel('Date')
ax2.set_title('NASA HTTP Traffic - Bytes Transferred Over Time')
ax2.legend()
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))

plt.tight_layout()
plt.savefig('outputs/eda/01_overall_traffic.png', dpi=150)
plt.close()
print("Saved: outputs/eda/01_overall_traffic.png")

# 4.2 Daily Pattern (Hourly aggregation)
df_valid['hour'] = df_valid['timestamp'].dt.hour
hourly_pattern = df_valid.groupby('hour')['request_count'].agg(['mean', 'std', 'min', 'max'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.fill_between(hourly_pattern.index, 
                hourly_pattern['mean'] - hourly_pattern['std'],
                hourly_pattern['mean'] + hourly_pattern['std'],
                alpha=0.3, label='+/-1 Std Dev')
ax.plot(hourly_pattern.index, hourly_pattern['mean'], 'b-', linewidth=2, label='Mean')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Request Count (per 5min)')
ax.set_title('Daily Traffic Pattern (Hourly Average)')
ax.set_xticks(range(0, 24))
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/eda/02_daily_pattern.png', dpi=150)
plt.close()
print("Saved: outputs/eda/02_daily_pattern.png")

# 4.3 Weekly Pattern
df_valid['dayofweek'] = df_valid['timestamp'].dt.dayofweek
daily_pattern = df_valid.groupby('dayofweek')['request_count'].agg(['mean', 'std'])
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(range(7), daily_pattern['mean'], yerr=daily_pattern['std'], capsize=5, alpha=0.7)
ax.set_xticks(range(7))
ax.set_xticklabels(days)
ax.set_xlabel('Day of Week')
ax.set_ylabel('Mean Request Count (per 5min)')
ax.set_title('Weekly Traffic Pattern')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('outputs/eda/03_weekly_pattern.png', dpi=150)
plt.close()
print("Saved: outputs/eda/03_weekly_pattern.png")

# 4.4 Distribution of Request Count
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
ax1 = axes[0]
ax1.hist(df_valid['request_count'], bins=50, edgecolor='black', alpha=0.7)
ax1.axvline(df_valid['request_count'].mean(), color='red', linestyle='--', label=f'Mean: {df_valid["request_count"].mean():.1f}')
ax1.axvline(df_valid['request_count'].median(), color='green', linestyle='--', label=f'Median: {df_valid["request_count"].median():.1f}')
ax1.set_xlabel('Request Count (per 5min)')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of Request Count')
ax1.legend()

# Box plot by month
df_valid['month'] = df_valid['timestamp'].dt.month
ax2 = axes[1]
df_valid.boxplot(column='request_count', by='month', ax=ax2)
ax2.set_xlabel('Month')
ax2.set_ylabel('Request Count')
ax2.set_title('Request Count by Month')
plt.suptitle('')  # Remove auto title

plt.tight_layout()
plt.savefig('outputs/eda/04_distribution.png', dpi=150)
plt.close()
print("Saved: outputs/eda/04_distribution.png")

# 4.5 Status Code Analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pie chart
ax1 = axes[0]
colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6']
ax1.pie(status_totals, labels=['2xx (Success)', '3xx (Redirect)', '4xx (Client Error)', '5xx (Server Error)'],
        autopct='%1.1f%%', colors=colors, startangle=90)
ax1.set_title('HTTP Status Code Distribution')

# Error rate over time
df_valid['error_rate'] = (df_valid['status_4xx'] + df_valid['status_5xx']) / df_valid['request_count'] * 100
df_valid['error_rate'] = df_valid['error_rate'].fillna(0)

ax2 = axes[1]
# Resample to daily for cleaner visualization
daily_errors = df_valid.set_index('timestamp')['error_rate'].resample('D').mean()
ax2.plot(daily_errors.index, daily_errors.values, marker='o', markersize=3)
ax2.set_xlabel('Date')
ax2.set_ylabel('Error Rate (%)')
ax2.set_title('Daily Average Error Rate (4xx + 5xx)')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/eda/05_status_codes.png', dpi=150)
plt.close()
print("Saved: outputs/eda/05_status_codes.png")

# 4.6 Spike Detection
# Define spike as > mean + 3*std
threshold = df_valid['request_count'].mean() + 3 * df_valid['request_count'].std()
df_valid['is_spike'] = df_valid['request_count'] > threshold
spikes = df_valid[df_valid['is_spike']]

print(f"\n--- Spike Detection (threshold: {threshold:.1f}) ---")
print(f"Number of spikes: {len(spikes)}")
print(f"Spike percentage: {len(spikes)/len(df_valid)*100:.2f}%")

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(df_valid['timestamp'], df_valid['request_count'], linewidth=0.5, alpha=0.7, label='Normal')
ax.scatter(spikes['timestamp'], spikes['request_count'], color='red', s=20, label=f'Spikes (>{threshold:.0f})')
ax.axhline(threshold, color='orange', linestyle='--', alpha=0.7, label=f'Threshold ({threshold:.0f})')
ax.axhline(df_valid['request_count'].mean(), color='green', linestyle='--', alpha=0.7, label=f'Mean ({df_valid["request_count"].mean():.0f})')
ax.set_xlabel('Date')
ax.set_ylabel('Request Count (per 5min)')
ax.set_title('Traffic Spike Detection')
ax.legend()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

plt.tight_layout()
plt.savefig('outputs/eda/06_spike_detection.png', dpi=150)
plt.close()
print("Saved: outputs/eda/06_spike_detection.png")

# 4.7 Train/Test Split Visualization
train_end = pd.Timestamp("1995-08-22 23:59:59", tz=df['timestamp'].dt.tz)

fig, ax = plt.subplots(figsize=(16, 6))
train_data = df[df['timestamp'] <= train_end]
test_data = df[df['timestamp'] > train_end]

ax.plot(train_data['timestamp'], train_data['request_count'], linewidth=0.5, label='Train', color='blue')
ax.plot(test_data['timestamp'], test_data['request_count'], linewidth=0.5, label='Test', color='orange')
ax.axvline(train_end, color='red', linestyle='--', linewidth=2, label='Train/Test Split')
ax.axvspan(outage_rows['timestamp'].min(), outage_rows['timestamp'].max(), 
           alpha=0.3, color='gray', label='Outage')
ax.set_xlabel('Date')
ax.set_ylabel('Request Count (per 5min)')
ax.set_title('Train/Test Split (Train: July + Aug 1-22, Test: Aug 23-31)')
ax.legend()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

plt.tight_layout()
plt.savefig('outputs/eda/07_train_test_split.png', dpi=150)
plt.close()
print("Saved: outputs/eda/07_train_test_split.png")

# ============================================================
# 5. SUMMARY REPORT
# ============================================================
print("\n" + "="*60)
print("5. EDA SUMMARY REPORT")
print("="*60)

summary = f"""
NASA HTTP Traffic - EDA Summary
================================

Dataset Overview:
- Time Period: {df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}
- Total Duration: {(df['timestamp'].max() - df['timestamp'].min()).days} days
- Resolution Used: 5-minute intervals
- Total Records: {len(df):,}

Missing Data (Outage):
- Outage Period: {outage_rows['timestamp'].min()} to {outage_rows['timestamp'].max()}
- Duration: ~37.7 hours
- Affected Records: {len(outage_rows):,} ({len(outage_rows)/len(df)*100:.2f}%)

Traffic Statistics (excluding outage):
- Mean Request Count: {df_valid['request_count'].mean():.2f} per 5min
- Std Dev: {df_valid['request_count'].std():.2f}
- Max Request Count: {df_valid['request_count'].max():.0f} per 5min
- Mean Bytes: {df_valid['total_bytes'].mean()/1e6:.2f} MB per 5min

Status Codes:
- 2xx (Success): {status_pct['status_2xx']:.1f}%
- 3xx (Redirect): {status_pct['status_3xx']:.1f}%
- 4xx (Client Error): {status_pct['status_4xx']:.1f}%
- 5xx (Server Error): {status_pct['status_5xx']:.1f}%

Patterns Observed:
- Daily Pattern: Traffic peaks during US business hours (10:00-16:00 EST)
- Weekly Pattern: Higher traffic on weekdays vs weekends
- Spikes Detected: {len(spikes)} instances (>{threshold:.0f} requests/5min)

Train/Test Split:
- Train: {len(train_data):,} records (July + Aug 1-22)
- Test: {len(test_data):,} records (Aug 23-31)
- Split Ratio: {len(train_data)/len(df)*100:.1f}% / {len(test_data)/len(df)*100:.1f}%

Generated Visualizations:
1. outputs/eda/01_overall_traffic.png
2. outputs/eda/02_daily_pattern.png
3. outputs/eda/03_weekly_pattern.png
4. outputs/eda/04_distribution.png
5. outputs/eda/05_status_codes.png
6. outputs/eda/06_spike_detection.png
7. outputs/eda/07_train_test_split.png
"""

print(summary)

# Save summary to file
with open('outputs/eda/eda_summary.txt', 'w') as f:
    f.write(summary)
print("\nSaved: outputs/eda/eda_summary.txt")

print("\n" + "="*60)
print("EDA COMPLETE!")
print("="*60)
