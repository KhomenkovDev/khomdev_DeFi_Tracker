import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_multitool.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.cache import cache

# Clear the cache to be absolutely sure we hit the code
cache.clear()

c = Client()
try:
    user = User.objects.create_user('testusr2', 'test2@test.com', 'pwd')
except:
    user = User.objects.get(username='testusr2')
c.login(username='testusr2', password='pwd')
res = c.get('/api/historical-data/?symbol=AAPL&period=5d')
print("Status Code:", res.status_code)
print("Response:", res.content[:200])
