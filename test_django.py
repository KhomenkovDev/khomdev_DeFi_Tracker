import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_multitool.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
c = Client()
user = User.objects.create_user('testusr', 'test@test.com', 'pwd')
c.login(username='testusr', password='pwd')
res = c.get('/api/historical-data/?symbol=AAPL&period=1mo')
print(res.json())
