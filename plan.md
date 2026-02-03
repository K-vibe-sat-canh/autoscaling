# Project Context: Autoscaling Analysis (NASA Log Data)

I am participating in a Data Science competition focused on Autoscaling Analysis for a web server. I have completed the Data Engineering and EDA phases. I need your help to proceed with **Phase 3 (Modeling)** and **Phase 4 (Optimization)**.

## 1. Project Structure & Current Status

Here is my local directory structure and the status of each component:

*   **Raw Data:** Located at `C:\Users\YAYSOOSWhite\Documents\autoscaling\DATA` (Original .txt/ASCII logs).
*   **EDA Outputs:** Located at `C:\Users\YAYSOOSWhite\Documents\autoscaling\outputs\eda` (Contains PNG plots and `summary.txt`).
*   **Processed Data:** Located at `C:\Users\YAYSOOSWhite\Documents\autoscaling\processed_data`.
    *   Format: `.csv` files.
    *   Status: Cleaned, regex parsed, timestamps normalized.
    *   Aggregations available: 1-minute, 10-minute, 15-minute windows.
    *   *Note:* The data covers July 1st, 1995 to August 31st, 1995. There is a known gap from Aug 1 (14:52) to Aug 3 (04:36) due to a hurricane.

## 2. Requirements (from Competition PDF)

I need Python code (using pandas, sklearn, statsmodels, or prophet) to perform the following steps based on the `processed_data` CSVs.

### A. Train/Test Split Logic (Strict Requirement)
The dataset must be split exactly as follows:
*   **Train Set:** All data from **July 1st** through **August 22nd**.
*   **Test Set:** All data from **August 23rd** through **August 31st**.

### B. Modeling Tasks (Phase 3)
I need to implement at least **02 distinct models** to forecast:
1.  **Requests per second (hits)**
2.  **Traffic volume (bytes)**

*Preferred Model Candidates:*
1.  **Prophet (Facebook):** To handle seasonality and the missing data gap gracefully.
2.  **XGBoost/LightGBM:** Using lag features (sliding window) as a strong Machine Learning baseline.
3.  *(Optional)* LSTM if simple models underperform.

*Evaluation Metrics:* RMSE, MSE, MAE, MAPE.

### C. Optimization & Scaling Logic (Phase 4)
Based on the forecast, implement a function that simulates autoscaling:
*   **Input:** Forecasted requests/bytes.
*   **Logic:**
    *   Determine number of servers needed (e.g., threshold-based).
    *   Implement **Cooldown/Hysteresis**: Don't scale up/down instantly to avoid "flapping" (e.g., maintain high capacity for 5 mins before scaling down).

## 3. Your Task

Please generate a **Python Notebook structure (or script)** that does the following:

1.  **Data Loading:** Code to load the CSVs from `C:\Users\YAYSOOSWhite\Documents\autoscaling\processed_data`.
2.  **Resampling:** Ensure we have a **5-minute** aggregation (the PDF specifically asks for 1m, 5m, 15m). If I only have 10m, please resample the 1m data to 5m.
3.  **Feature Engineering:** Create time-based features (hour, day of week) and lag features for the ML model.
4.  **Model Training:**
    *   Implement **Prophet** for the time series.
    *   Implement **XGBoost** (or similar) for regression.
5.  **Evaluation:** Calculate and print RMSE/MAE for the Test period (Aug 23 - Aug 31).
6.  **Visualization:** Plot Actual vs. Predicted values for the Test set.

Please keep the code clean, modular, and use the specified file paths.