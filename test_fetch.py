import urllib.request
import json

req = urllib.request.Request("http://127.0.0.1:8000/api/historical-data/?symbol=AAPL&period=1mo")
# We need to bypass login_required or disable it temporarily or test with a simulated client.
