from flask import Flask, render_template
import requests
import pandas as pd
import ta
import plotly.graph_objs as go
import plotly.io as pio

app = Flask(__name__)

def get_data():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=["time","open","high","low","close","volume",
                                     "close_time","qav","trades","tbbav","tbqav","ignore"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    return df

def generate_signals(df):
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
    df = get_data()
    df = generate_signals(df)
    last_signal = df["signal"].iloc[-1] if df["signal"].iloc[-1] else "HOLD"
    rsi = round(df["rsi"].iloc[-1],2)
    chart = make_plot(df)
    return render_template("index.html", signal=last_signal, rsi=rsi, chart=chart)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
