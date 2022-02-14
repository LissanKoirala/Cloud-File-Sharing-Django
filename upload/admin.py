from django.contrib import admin
from .models import File

# Register your models here.

class FileAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_name', 'shared', 'file_size', 'data_last_modified')
    list_filter = ('data_last_modified', 'in_bin', 'shared', 'user')
    search_fields = ('file_name', )

    list_display_links = ('file_name', 'user')
    
admin.site.register(File, FileAdmin)

