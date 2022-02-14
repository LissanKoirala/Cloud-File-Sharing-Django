from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Device(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	hostname = models.CharField(null=False, max_length=200)
	date_device_added = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.hostname