from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path as url
from django.shortcuts import render 
from . import views
from django.conf import settings 

app_name = 'home'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('folder/<int:folder_id>/', views.FolderDetailView.as_view(), name='folder_detail'),

    path('create_folder/',  views.CreateFolderView.as_view(), name='create_folder'),
    path('folder/<int:folder_id>/upload/', views.upload_file_view, name='upload_file'),
    path('folder/<int:folder_id>/invite/', views.InviteUserToFolderView.as_view(), name='invite_user_to_folder'),
    path('invitation/<int:invitation_id>/accept/', views.AcceptFolderInvitationView.as_view(), name='accept_folder_invitation'),

]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
