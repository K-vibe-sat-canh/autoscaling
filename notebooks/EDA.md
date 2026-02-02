# 📊 EDA (Exploratory Data Analysis) - Placeholder

> **Note:** This is a placeholder notebook. In the full project, this would be a Jupyter Notebook (.ipynb) with:
> - Data loading and inspection
> - Missing value analysis
> - Time-series visualization
> - Feature correlation

## What would be in a real EDA notebook:

### 1. Data Loading
```python
import pandas as pd
df = pd.read_csv('data/clean_data.csv')
df.info()
df.describe()
```

### 2. Time Series Plot
```python
import matplotlib.pyplot as plt
df['timestamp'] = pd.to_datetime(df['timestamp'])
plt.figure(figsize=(15, 5))
plt.plot(df['timestamp'], df['requests'])
plt.title('HTTP Requests Over Time')
plt.xlabel('Date')
plt.ylabel('Requests/minute')
plt.show()
```

### 3. Detect the "Storm" Period
```python
# Find the gap in data (01/08 - 03/08)
df['date'] = df['timestamp'].dt.date
daily_counts = df.groupby('date').size()
print("Dates with missing data:")
print(daily_counts[daily_counts < 1000])
```

### 4. Hourly Pattern
```python
df['hour'] = df['timestamp'].dt.hour
hourly_avg = df.groupby('hour')['requests'].mean()
hourly_avg.plot(kind='bar')
plt.title('Average Traffic by Hour')
```

### 5. Key Insights
- Peak hours: 12:00 - 18:00
- Low hours: 02:00 - 06:00
- Storm period: 01/08 14:52 to 03/08 04:36
- Weekend vs Weekday: Similar patterns

---

**For the full notebook, run:**
```bash
jupyter notebook notebooks/EDA.ipynb
```

**Or use the data directly with:**
```bash
python src/data_pipeline.py  # Generates data
python src/model_trainer.py  # Trains model with EDA-like output
```
