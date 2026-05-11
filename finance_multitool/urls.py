from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    # NOTE: We no longer include django.contrib.auth.urls because we have
    # custom login/logout views that fix the password authentication bug.
    # django.contrib.auth.urls would override our custom login view.
]
