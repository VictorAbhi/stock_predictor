import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

# Streamlit UI setup
st.set_page_config(page_title="Stock Price Forecasting", layout="wide")
st.title("📈 Stock Price Forecasting for CBBL, NABIL, and SADBL")

# Sidebar - Company Selection
company_choice = st.sidebar.selectbox("Choose Company", ["CBBL", "NABIL", "SADBL"])

# Load Data based on selected company
file_paths = {
    "CBBL": "C:/Users/adabh/Documents/nepal_finance_institution_stock_predictor/Data_sets/CBBL_price_history.csv",
    "NABIL": "C:/Users/adabh/Documents/nepal_finance_institution_stock_predictor/Data_sets/NABIL_price_history.csv",
    "SADBL": "C:/Users/adabh/Documents/nepal_finance_institution_stock_predictor/Data_sets/SADBL_price_history.csv"
}

try:
    df = pd.read_csv(file_paths[company_choice])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Drop rows where 'Date' or 'Ltp' is NaT or NaN
    df.dropna(subset=['Date', 'Ltp'], inplace=True)

    df.sort_values(by='Date', ascending=True, inplace=True)
    df = df[df['Date'] >= '2015-01-01']
    
    # Remove commas from 'Ltp' and convert it to numeric
    df['Ltp'] = df['Ltp'].astype(str).str.replace(',', '', regex=False)
    df['Ltp'] = pd.to_numeric(df['Ltp'], errors='coerce')

    df.set_index('Date', inplace=True)
    print(df.head())

except FileNotFoundError:
    st.error(f"Data file for {company_choice} not found.")
    st.stop()


# Load the corresponding LSTM model for the selected company
model_path = f"C:/Users/adabh/Documents/nepal_finance_institution_stock_predictor/ML_model/{company_choice}_lstm_model.h5"
try:
    lstm_model = load_model(model_path)
except OSError:
    st.error(f"Model file for {company_choice} not found.")
    st.stop()

# Normalize Data for LSTM
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(df['Ltp'].values.reshape(-1, 1))

# Sidebar - Forecast Steps
forecast_steps = st.sidebar.slider("Select Forecast Steps", 1, 60, 30)

# Forecast using LSTM
sequence_length = 30
last_sequence = scaled_data[-sequence_length:].reshape((1, sequence_length, 1))

lstm_forecast = []
for _ in range(forecast_steps):
    pred = lstm_model.predict(last_sequence)[0, 0]
    lstm_forecast.append(pred)
    last_sequence = np.append(last_sequence[:, 1:, :], [[[pred]]], axis=1)

# Inverse scaling
lstm_forecast = scaler.inverse_transform(np.array(lstm_forecast).reshape(-1, 1))

# Evaluate Model
test_size = int(len(df) * 0.2)
test = df[-test_size:]

# Calculate MSE, RMSE, and R² Score
mse_lstm = mean_squared_error(test['Ltp'][:forecast_steps], lstm_forecast[:forecast_steps])
rmse_lstm = np.sqrt(mse_lstm)
r2_lstm = r2_score(test['Ltp'][:forecast_steps], lstm_forecast[:forecast_steps])

# Plot Results
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df.index[-100:], df['Ltp'][-100:], label="Actual Data", color="blue")

# Generate future dates for plotting
future_dates = pd.date_range(df.index[-1], periods=forecast_steps + 1, freq='D')[1:]

ax.plot(future_dates, lstm_forecast, label="LSTM Forecast", color="red", linestyle="--")

ax.legend()
ax.grid(True)
ax.set_title(f"LSTM Model Forecast for {company_choice}")
ax.set_xlabel("Date")
ax.set_ylabel("Stock Price (Ltp)")
st.pyplot(fig)

# Show Model Performance
st.sidebar.subheader("📊 Model Performance")
st.sidebar.write(f"**LSTM RMSE for {company_choice}:** {rmse_lstm:.4f}")
st.sidebar.write(f"**LSTM R² Score for {company_choice}:** {r2_lstm:.4f}")
