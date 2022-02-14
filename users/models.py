from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    account_activated = models.BooleanField(default=False)

    activation_id = models.CharField(max_length=500, blank=True)

    folder_id = models.CharField(max_length=500, blank=True)

    storage = models.IntegerField(default=2)

    def __str__(self):
    	return self.user.username

    def save(self, *args, **kawrgs):
        super().save(*args, **kawrgs)
