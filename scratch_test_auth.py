import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_multitool.settings')
django.setup()

from dashboard.views import register

def test_register():
    rf = RequestFactory()
    # Create a POST request to register
    data = {
        'username': 'newuser1',
        'password': 'password123',
        'password_confirm': 'password123', # Wait, UserCreationForm uses password1 and password2
    }
    # Let's check what fields UserCreationForm expects
    from django.contrib.auth.forms import UserCreationForm
    form = UserCreationForm()
    print(f"Form fields: {form.fields.keys()}")

test_register()
