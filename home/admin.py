from django.contrib import admin
from .models import *

# Register your custom User model with the custom UserAdmin class

# Register your Folder and File models
admin.site.register(Folder)
admin.site.register(File)
admin.site.register(FolderInvitation)
admin.site.register(FileInvitation)
