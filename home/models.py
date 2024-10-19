from django.db import models
from django.contrib.auth.models import User
from django.db.models import CASCADE, ForeignKey
from django.urls import reverse
import uuid
from django.core.exceptions import ValidationError
import os



def file(instance, filename):
    unique_id = str(uuid.uuid4())
    directory_path = f'content/{unique_id}/'
    return os.path.join(directory_path, filename)


# Assuming you have a function called validate_file_extension
def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_folders')
    users_with_access = models.ManyToManyField(User, related_name='accessible_folders', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('home:folder_detail', kwargs={'pk': self.pk})

class File(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files', null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='file', validators=[validate_file_extension], null=True, blank=True)  # Use FileField for file uploads
    file_size = models.BigIntegerField(null=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name if self.name else self.file.name

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('home:file_detail', kwargs={'pk': self.pk})

class FolderInvitation(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folder_invitations')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_folder_invitations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation to {self.folder.name} for {self.invited_user.username}" 

class FileInvitation(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invited_user.username} invited to {self.file.name} by {self.sender.username}"