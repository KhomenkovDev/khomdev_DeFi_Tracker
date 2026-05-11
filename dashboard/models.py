from django.contrib.auth.models import User
from django.db import models


class UserAsset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "symbol"], name="unique_user_symbol")
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.symbol}"
