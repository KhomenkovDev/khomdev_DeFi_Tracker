from django.db import models
from django.contrib.auth.models import User

class UserAsset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'symbol')
        
    def __str__(self):
        return f"{self.user.username} - {self.symbol}"
