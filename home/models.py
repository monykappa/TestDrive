from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
import uuid

# Utility to store file in a unique folder path
def file(instance, filename):
    unique_id = str(uuid.uuid4())
    directory_path = f'content/{unique_id}/'
    return os.path.join(directory_path, filename)

# Function to validate file extensions
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

# Folder Model (applies to both personal and team folders)
class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_folders')  # Folder creator (for personal)
    users_with_access = models.ManyToManyField(User, related_name='accessible_folders', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name

    def is_team_folder(self):
        return self.is_team_folder

# File Model (inside folders)
class File(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files', null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=file, validators=[validate_file_extension], null=True, blank=True)
    file_size = models.BigIntegerField(null=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name if self.name else self.file.name

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

# TeamFolder Model (for team folders)
class TeamFolder(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_team_folders')  # Team folder creator
    users_with_access = models.ManyToManyField(User, through='TeamFolderPermission', related_name='accessible_team_folders', blank=True)  # Permissions for access
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

# TeamFolderPermission model to define access and permissions within team folders
class TeamFolderPermission(models.Model):
    team_folder = models.ForeignKey(TeamFolder, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_share = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    class Meta:
        unique_together = ('team_folder', 'user')  # Ensures a user can't have duplicate permissions for a team folder

    def __str__(self):
        return f"{self.user.username}'s permissions for {self.team_folder.name}"

# File Model (for files inside team folders)
class TeamFolderFile(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    team_folder = models.ForeignKey(TeamFolder, on_delete=models.CASCADE, related_name='files', null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_folder_files')
    file = models.FileField(upload_to=file, validators=[validate_file_extension], null=True, blank=True)
    file_size = models.BigIntegerField(null=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name if self.name else self.file.name

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

# Folder Invitation for sharing team folders
class FolderInvitation(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folder_invitations')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_folder_invitations')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Invitation to {self.folder.name} for {self.invited_user.username}"

# File Invitation for sharing files in team folders
class FileInvitation(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.invited_user.username} invited to {self.file.name} by {self.sender.username}"
