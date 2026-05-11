from __future__ import annotations

import os

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db import connection
from django.http import JsonResponse


@staff_member_required
def debug_auth_status(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "Not available"}, status=404)

    db_engine = connection.settings_dict.get("ENGINE", "")
    is_sqlite = "sqlite" in db_engine
    users = list(User.objects.values_list("username", flat=True))

    return JsonResponse(
        {
            "auth_status": {
                "is_authenticated": request.user.is_authenticated,
                "username": str(request.user) if request.user.is_authenticated else None,
                "session_key": request.session.session_key,
            },
            "database": {
                "engine": db_engine,
                "is_sqlite_warning": is_sqlite,
            },
            "ai_config": {
                "claude_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY")),
                "active_ai": (
                    "claude"
                    if os.environ.get("ANTHROPIC_API_KEY")
                    else (
                        "gemini"
                        if os.environ.get("GEMINI_API_KEY")
                        else "none"
                    )
                ),
            },
        }
    )
