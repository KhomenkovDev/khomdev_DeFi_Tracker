from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("dashboard_home")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = field if field == "__all__" else field.capitalize()
                    if label == field:
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{label}: {error}")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both your username and password.")
            return render(request, "registration/login.html", {"username": username})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or "dashboard_home"
            return redirect(next_url)
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Incorrect password. Please try again.")
            else:
                messages.error(
                    request,
                    f"No account found for '{username}'. Please register first.",
                )

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")
