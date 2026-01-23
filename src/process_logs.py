"""
NASA HTTP Log Processor
Parses train.txt and test.txt, aggregates data into 1m, 5m, and 15m intervals
Follows the pipeline from note.md:
- Regex 1: parse host/timestamp/request/status/bytes
- Regex 2: parse request into method/url/protocol
- Resample: count + sum(bytes) + status groups
- Outage: mark + mask NaN for 01/08-03/08 period
"""

import re
import pandas as pd
from datetime import datetime
import os

# === REGEX PATTERNS ===

# Regex 1: Parse log line into host/timestamp/request/status/bytes
LOG_RE = re.compile(
    r'^(?P<host>\S+)\s+'          # host/ip
    r'\S+\s+\S+\s+'               # ignore ident/user (- -)
    r'\[(?P<ts>[^\]]+)\]\s+'      # [23/Aug/1995:00:00:00 -0400]
    r'"(?P<request>[^"]*)"\s+'    # "GET /... HTTP/1.0"
    r'(?P<status>\d{3})\s+'       # 200
    r'(?P<bytes>\S+)\s*$'         # 7087 or -
)

# Regex 2: Parse request into method/url/protocol
REQ_RE = re.compile(
    r'^(?P<method>\S+)\s+(?P<url>\S+)(?:\s+(?P<protocol>\S+))?$'
)

# === OUTAGE PERIOD ===
OUTAGE_START = pd.Timestamp("1995-08-01 14:52:01-04:00")
OUTAGE_END   = pd.Timestamp("1995-08-03 04:36:13-04:00")


def parse_ts(ts: str):
    """Parse timestamp with timezone"""
    # '%z' reads offset -0400
    return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")


def parse_log_file(path: str) -> pd.DataFrame:
    """Parse a log file into DataFrame with all fields"""
    rows = []
    line_count = 0
    matched_count = 0
    
    print(f"Processing: {path}")
    
    with open(path, "r", encoding="latin-1", errors="replace") as f:
        for line in f:
            line_count += 1
            line = line.rstrip("\n")
            m = LOG_RE.match(line)
            if not m:
                continue
            
            matched_count += 1
            d = m.groupdict()

            # timestamp
            try:
                ts = parse_ts(d["ts"])
            except:
                continue

            # status
            status = int(d["status"])

            # bytes: '-' => NaN
            b = d["bytes"]
            bytes_ = None if b == "-" else int(b)

            # request split
            req = d["request"]
            method = url = protocol = None
            rm = REQ_RE.match(req)
            if rm:
                method = rm.group("method")
                url = rm.group("url")
                protocol = rm.group("protocol")

            rows.append({
                "timestamp": ts,
                "host": d["host"],
                "method": method,
                "url": url,
                "protocol": protocol,
                "status": status,
                "bytes": bytes_,
            })
    
    print(f"  Total lines: {line_count:,}")
    print(f"  Matched: {matched_count:,}")
    print(f"  Match rate: {matched_count/line_count*100:.2f}%" if line_count > 0 else "  No lines")

    df = pd.DataFrame(rows)
    if len(df) > 0:
        # Ensure proper types
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        df["status"] = df["status"].astype("int16")
    return df


def make_traffic_ts(df_log: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Resample log data into traffic time series with status breakdown"""
    d = df_log.copy()
    d = d.set_index("timestamp").sort_index()

    # bytes NaN -> 0 for sum
    bytes_series = d["bytes"].fillna(0)

    base = pd.DataFrame({
        "request_count": d["status"].resample(freq).size(),
        "total_bytes": bytes_series.resample(freq).sum(),
    })

    # status groups
    s = d["status"]
    base["status_2xx"] = (s.between(200, 299)).resample(freq).sum()
    base["status_3xx"] = (s.between(300, 399)).resample(freq).sum()
    base["status_4xx"] = (s.between(400, 499)).resample(freq).sum()
    base["status_5xx"] = (s.between(500, 599)).resample(freq).sum()

    base = base.reset_index()  # timestamp back to column
    return base


def apply_outage_mask(ts_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Mark outage period and mask metrics with NaN"""
    t = ts_df.copy()
    t["timestamp"] = pd.to_datetime(t["timestamp"])
    t = t.set_index("timestamp").sort_index()

    # reindex to fill all time slots
    full_idx = pd.date_range(t.index.min(), t.index.max(), freq=freq, tz=t.index.tz)
    t = t.reindex(full_idx)

    # mark outage (timestamps within range)
    is_outage = (t.index > OUTAGE_START) & (t.index < OUTAGE_END)
    t["is_outage"] = is_outage.astype("int8")

    # mask metrics during outage
    metric_cols = [c for c in t.columns if c != "is_outage"]
    t.loc[is_outage, metric_cols] = pd.NA

    return t.reset_index(names="timestamp")


def main():
    base_dir = r'c:\Users\eleven\Documents\AUTOSCALING_ANALYSIS'
    data_dir = os.path.join(base_dir, 'DATA')
    output_dir = os.path.join(base_dir, 'processed_data')
    
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse both files
    all_dfs = []
    
    # Process train.txt
    train_file = os.path.join(data_dir, 'train.txt')
    if os.path.exists(train_file):
        df = parse_log_file(train_file)
        all_dfs.append(df)
        print(f"  Records from train.txt: {len(df):,}\n")
    
    # Process test.txt
    test_file = os.path.join(data_dir, 'test.txt')
    if os.path.exists(test_file):
        df = parse_log_file(test_file)
        all_dfs.append(df)
        print(f"  Records from test.txt: {len(df):,}\n")
    
    if not all_dfs:
        print("No log files found!")
        return
    
    # Combine all dataframes
    df_log = pd.concat(all_dfs, ignore_index=True)
    print(f"Total records: {len(df_log):,}")
    
    # Save raw parsed data (Layer 1: Detailed Log w/ Path)
    # Note: Saving to CSV as safer option if parquet engines are missing
    raw_output = os.path.join(output_dir, 'nasa_logs_parsed.csv')
    print(f"Saving Layer 1 (Detailed Parsed Logs) to: {raw_output} ...")
    df_log.to_csv(raw_output, index=False)
    print("  Done.")
    
    # Create aggregations with outage handling
    print("\n--- Creating Aggregations with Outage Handling ---")
    
    for freq, suffix in [("1min", "1m"), ("5min", "5m"), ("15min", "15m")]:
        print(f"\nGenerating {suffix} aggregation...")
        
        # Create traffic time series
        ts_df = make_traffic_ts(df_log, freq)
        
        # Apply outage mask
        ts_df = apply_outage_mask(ts_df, freq)
        
        # Save to CSV
        output_file = os.path.join(output_dir, f'nasa_traffic_{suffix}.csv')
        ts_df.to_csv(output_file, index=False)
        print(f"  Saved: {output_file}")
        print(f"  Rows: {len(ts_df):,}")
        
        # Stats
        non_outage = ts_df[ts_df["is_outage"] == 0]
        if len(non_outage) > 0:
            print(f"  Non-outage rows: {len(non_outage):,}")
            print(f"  Total requests (non-outage): {non_outage['request_count'].sum():,.0f}")
    
    # Summary
    print("\n--- Summary ---")
    ts_1m = pd.read_csv(os.path.join(output_dir, 'nasa_traffic_1m.csv'))
    print(f"Date range: {ts_1m['timestamp'].min()} to {ts_1m['timestamp'].max()}")
    
    outage_rows = ts_1m[ts_1m["is_outage"] == 1]
    print(f"Outage periods (1m bins): {len(outage_rows):,}")
    
    non_outage = ts_1m[ts_1m["is_outage"] == 0]
    print(f"Total requests (non-outage): {non_outage['request_count'].sum():,.0f}")
    print(f"Total bytes (non-outage): {non_outage['total_bytes'].sum():,.0f}")


if __name__ == '__main__':
    main()
