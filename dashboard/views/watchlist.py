from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import UserAsset

logger = logging.getLogger(__name__)


@login_required
def api_toggle_watchlist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        symbol = data.get("symbol")
        name = data.get("name", symbol)
        asset, created = UserAsset.objects.get_or_create(user=request.user, symbol=symbol)
        if not created:
            asset.delete()
            return JsonResponse({"status": "removed", "symbol": symbol})
        else:
            asset.name = name
            asset.save()
            return JsonResponse({"status": "added", "symbol": symbol})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception:
        logger.exception("Failed to toggle watchlist for %s", request.user.username)
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
