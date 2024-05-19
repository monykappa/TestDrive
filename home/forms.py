from django import forms
from .models import *
from django.core.validators import FileExtensionValidator
from django.core.validators import MaxValueValidator, MinValueValidator
# from django.core.validators import FileExtensionValidator, FileValidator   
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']        
class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['name', 'file']

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    if not ext.lower() in valid_extensions:
        raise forms.ValidationError('Unsupported file extension.')
    
