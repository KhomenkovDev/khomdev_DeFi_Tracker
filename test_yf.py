import yfinance as yf
ticker = yf.Ticker('AAPL')
hist = ticker.history(period='1mo')
for date, row in hist.iterrows():
    print(date.strftime('%Y-%m-%d'), round(row['Open'], 2))
