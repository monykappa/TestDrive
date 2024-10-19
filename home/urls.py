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
    
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register, name='register'),
    
    # path('shared/', views.SharedFoldersView.as_view(), name='shared_folders'),
    path('my_folders/', views.MyFoldersView.as_view(), name='my_folders'),
    path('delete_folder/<int:folder_id>/', views.DeleteFolderView.as_view(), name='delete_folder'),
    path('add_folder/', views.AddFolderView.as_view(), name='add_folder'),
    path('share_folder/', views.ShareFolderView.as_view(), name='share_folder'),
    path('share-folder/<int:folder_id>/', views.ShareFolderView.as_view(), name='share_folder'),  # Add this line
    path('share-personal-folder/', views.SharePersonalFolder.as_view(), name='share_personal_folder'),
    path('file/share/<int:file_id>/', views.ShareFileView.as_view(), name='share_file'),
    path('file/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('shared_content/', views.SharedContentView.as_view(), name='shared_content'),


]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
