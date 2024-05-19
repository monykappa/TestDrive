from gettext import translation
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
from django.views import View
from .forms import *
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
import datetime
from django.utils import timezone


class FolderDetailView(View):
    def get(self, request, folder_id):
        folder = Folder.objects.get(id=folder_id)
        files = folder.files.all()  # Fetch all files related to the folder
        subfolders = folder.children.all()
        form = FolderForm()  # Form for creating a new folder
        return render(
            request,
            "home/folder_detail.html",
            {"folder": folder, "files": files, "subfolders": subfolders, "form": form},
        )

    def post(self, request, folder_id):
        folder = Folder.objects.get(id=folder_id)
        form = FolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.owner = request.user
            new_folder.parent = folder  # Set the parent folder
            new_folder.save()
            return redirect(
                "home:folder_detail", folder_id=folder_id
            )  # Redirect back to the same folder detail page
        else:
            files = folder.files.all()
            return render(
                request,
                "home/folder_detail.html",
                {"folder": folder, "files": files, "form": form},
            )

        

def upload_file_view(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.folder = folder
            file_instance.owner = request.user
            file_instance.file_size = request.FILES['file'].size
            file_instance.content_type = request.FILES['file'].content_type
            file_instance.save()
            # Redirect to the folder_detail view
            return HttpResponseRedirect(reverse('home:folder_detail', kwargs={'folder_id': folder.pk}))

    else:
        form = FileForm()
    files = folder.files.all()
    subfolders = folder.children.all()
    folder_form = FolderForm()
    return render(request, 'home/folder_detail.html', {
        'form': form,
        'folder': folder,
        'files': files,
        'subfolders': subfolders,
        'folder_form': folder_form
    })

class CreateFolderView(View):
    def get(self, request):
        form = FolderForm()
        folders = Folder.objects.filter(parent__isnull=True, owner=request.user)  # Assuming you want to show top-level folders
        return render(request, "home/create_folder.html", {"form": form, "folders": folders})

    def post(self, request):
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = request.user
            folder.save()
            form = FolderForm()  # Clear the form after successful submission
            # Retrieve updated list of folders
            folders = Folder.objects.filter(parent__isnull=True, owner=request.user)
            return redirect('home')  # Redirect to the home page after creating a folder
        else:
            # In case of form errors, render the form with errors
            folders = Folder.objects.filter(parent__isnull=True, owner=request.user)
            return render(request, "home/create_folder.html", {"form": form, "folders": folders})
        

class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            # Get folders owned by the user
            owned_folders = Folder.objects.filter(owner=user)
            # Get folders the user has access to, including those they've been invited to
            accessible_folders = Folder.objects.filter(
                Q(owner=user) | Q(users_with_access=user)
            ).distinct()
            # Get folders the user has been invited to
            invited_folders = Folder.objects.filter(invitations__invited_user=user)
            form = FolderForm()
            return render(request, "home/home.html", {
                "owned_folders": owned_folders,
                "accessible_folders": accessible_folders,
                "invited_folders": invited_folders,
                "form": form
            })
        else:
            return render(request, "home/home.html")

    def post(self, request):
        if request.user.is_authenticated:
            form = FolderForm(request.POST)
            if form.is_valid():
                folder = form.save(commit=False)
                folder.owner = request.user
                folder.save()
                return redirect('home:home')  # Redirect to the same page after successful form submission
            else:
                folders = Folder.objects.filter(owner=request.user)
                return render(request, "home/home.html", {"form": form, "folders": folders})
        else:
            return render(request, "home/home.html")  # Render home page without form for unauthenticated users


        
class InviteUserToFolderView(LoginRequiredMixin, View):
    def post(self, request, folder_id):
        folder = get_object_or_404(Folder, id=folder_id)
        invited_username = request.POST.get('invited_username')
        invited_user = User.objects.get(username=invited_username)
        
        # Check if the user is already invited or has access
        if folder.invitations.filter(invited_user=invited_user).exists() or folder.users_with_access.filter(id=invited_user.id).exists():
            return self.redirect_to_referer(request)
        
        # Send invitation
        invitation = FolderInvitation(folder=folder, invited_user=invited_user, sender=request.user)
        invitation.save()
        
        return self.redirect_to_referer(request)

    def redirect_to_referer(self, request):
        referer = request.POST.get('referer')
        if referer:
            return redirect(referer)
        else:
            return redirect('home:home')



class AcceptFolderInvitationView(LoginRequiredMixin, View):
    def post(self, request, invitation_id):
        invitation = get_object_or_404(FolderInvitation, id=invitation_id)
        folder = invitation.folder
        
        # Add user to folder's access list
        folder.users_with_access.add(request.user)
        
        # Delete the invitation
        invitation.delete()
        
        return redirect('home:folder_detail', folder_id=folder.id)