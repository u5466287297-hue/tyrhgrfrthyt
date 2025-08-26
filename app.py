from flask import Flask, render_template, request
import pandas as pd
import ta
import yfinance as yf
import plotly.graph_objs as go
import plotly.io as pio

app = Flask(__name__)

# Списък с най-популярните Forex двойки (Yahoo Finance символи)
FOREX_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/CAD": "EURCAD=X",
    "AUD/JPY": "AUDJPY=X",
    "NZD/JPY": "NZDJPY=X",
}

def get_forex_data(symbol="EURUSD=X"):
    try:
        df = yf.download(symbol, interval="1m", period="2d")
        df = df.reset_index()
        df.rename(columns={"Datetime":"time","Open":"open","High":"high","Low":"low","Close":"close"}, inplace=True)
        return df
    except Exception as e:
        print("Error loading data:", e)
        return pd.DataFrame()

def generate_signals(df):
    if df.empty:
        return df
    # Donchian Channel (30)
    df["donchian_high"] = df["high"].rolling(30).max()
    df["donchian_low"] = df["low"].rolling(30).min()
    # RSI (14)
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()

    signals = []
    for i in range(len(df)):
        sig = None
        if df["close"].iloc[i] > df["donchian_high"].iloc[i] and df["rsi"].iloc[i] > 50:
            sig = "BUY"
        elif df["close"].iloc[i] < df["donchian_low"].iloc[i] and df["rsi"].iloc[i] < 50:
            sig = "SELL"
        signals.append(sig)
    df["signal"] = signals
    return df

def make_plot(df):
    if df.empty:
        return "<p style='color:red'>No data available</p>"
    fig = go.Figure(data=[go.Candlestick(x=df["time"],
                                         open=df["open"],
                                         high=df["high"],
                                         low=df["low"],
                                         close=df["close"],
                                         name="Candles")])
    # BUY signals
    buys = df[df["signal"]=="BUY"]
    fig.add_trace(go.Scatter(x=buys["time"], y=buys["close"],
                             mode="markers", marker=dict(color="cyan", size=12, symbol="triangle-up"),
                             name="BUY"))
    # SELL signals
    sells = df[df["signal"]=="SELL"]
    fig.add_trace(go.Scatter(x=sells["time"], y=sells["close"],
                             mode="markers", marker=dict(color="magenta", size=12, symbol="triangle-down"),
                             name="SELL"))

    fig.update_layout(template="plotly_dark", 
                      paper_bgcolor="black", plot_bgcolor="black",
                      font=dict(color="#0ff"),
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                      margin=dict(l=20,r=20,t=40,b=20))
    return pio.to_html(fig, full_html=False)

@app.route("/")
def home():
    # Взимаме избрания символ от GET параметър
    symbol = request.args.get("symbol", "EURUSD=X")
    df = get_forex_data(symbol)
    df = generate_signals(df)

    if df.empty:
        last_signal = "HOLD"
        rsi = "N/A"
    else:
        last_signal = df["signal"].iloc[-1]
        if pd.isna(last_signal) or last_signal is None:
            last_signal = "HOLD"
        rsi = round(df["rsi"].iloc[-1],2) if not pd.isna(df["rsi"].iloc[-1]) else "N/A"

    chart = make_plot(df)
    return render_template("index.html", signal=last_signal, rsi=rsi, chart=chart, symbol=symbol, pairs=FOREX_PAIRS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
