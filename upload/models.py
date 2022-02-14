from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html
# Create your models here.


class File(models.Model):

	file_name = models.CharField(max_length=500, blank=True)

	file_size = models.IntegerField(blank=True, default=0)

	user = models.ForeignKey(User, on_delete=models.CASCADE)

	shared = models.BooleanField(default=False)

	share_id = models.CharField(max_length=500, blank=True)

	server_location = models.CharField(max_length=500, blank=True)

	data_last_modified = models.DateTimeField(default=timezone.now)

	in_bin = models.BooleanField(default=False)

	def __str__(self):
		return self.file_name

