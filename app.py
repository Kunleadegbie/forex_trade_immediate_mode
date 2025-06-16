import streamlit as st
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os
from streamlit_autorefresh import st_autorefresh

# === Configurable constants
EMAIL_ADDRESS = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

SIGNAL_LOG_FILE = 'trade_immediate_signal_log.csv'

# Fetch simulated market price and sentiment
def fetch_market_data():
    price = np.random.uniform(1.1000, 1.1500)
    sentiment = np.random.choice(['Bullish', 'Bearish', 'Neutral'])
    return round(price, 5), sentiment

# Signal generation logic (risk-averse)
def generate_signal(price):
    if price > 1.1450:
        return "SELL"
    elif price < 1.1050:
        return "BUY"
    else:
        return "NO TRADE"

# Log signals
def log_signal(time, signal, price, stop_loss):
    file_exists = os.path.isfile(SIGNAL_LOG_FILE)
    with open(SIGNAL_LOG_FILE, 'a') as f:
        if not file_exists:
            f.write('Time,Signal,Price,Stop Loss\n')
        f.write(f"{time},{signal},{price},{stop_loss}\n")

# Load signal log
def load_signal_log():
    if os.path.isfile(SIGNAL_LOG_FILE):
        return pd.read_csv(SIGNAL_LOG_FILE)
    else:
        return pd.DataFrame(columns=['Time', 'Signal', 'Price', 'Stop Loss'])

# Email notification function
def send_email(subject, body):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Email error: {e}")

# Main app
def main():
    st.set_page_config(page_title="Forex - Trade Immediately Mode", layout="wide")
    st.title("🚀 Forex Signal - Trade Immediately Mode")

    # Control Panel
    with st.sidebar:
        st.header("Settings")
        stop_loss_pips = st.number_input("Stop-Loss (pips)", min_value=5, max_value=50, value=20)
        refresh_interval = st.number_input("Auto-Refresh (secs)", min_value=10, max_value=300, value=60)

    st_autorefresh(interval=refresh_interval * 1000, key="data_refresh")

    price, sentiment = fetch_market_data()

    col1, col2 = st.columns(2)
    col1.metric("EUR/USD Price", f"{price:.5f}")
    col2.metric("Market Sentiment", sentiment)

    signal = generate_signal(price)
    st.subheader(f"📢 Current Signal: **{signal}**")

    # Process and log new signals
    if os.path.exists(SIGNAL_LOG_FILE):
        prev_log = pd.read_csv(SIGNAL_LOG_FILE)
        last_signal = prev_log['Signal'].iloc[-1] if not prev_log.empty else None
    else:
        last_signal = None

    if signal != last_signal and signal in ['BUY', 'SELL']:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stop_loss_distance = stop_loss_pips / 10000
        stop_loss = round(price - stop_loss_distance if signal == "BUY" else price + stop_loss_distance, 5)
        
        log_signal(now, signal, price, stop_loss)
        st.success(f"{signal} at {now} | Price: {price:.5f} | SL: {stop_loss:.5f}")

        # Send email notification
        message = f"""
🚨 Forex {signal} Signal 🚨
Time: {now}
Price: {price:.5f}
Stop Loss: {stop_loss:.5f}
"""
        send_email(f"Forex {signal} Signal Alert", message)

    st.divider()
    st.subheader("📜 Trade Signal Log")
    log_df = load_signal_log()
    st.dataframe(log_df, use_container_width=True)

    csv = log_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Signal Log (CSV)", data=csv, file_name='trade_immediate_signal_log.csv', mime='text/csv')

if __name__ == "__main__":
    main()
