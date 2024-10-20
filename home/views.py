from gettext import translation
import json
from msilib.schema import ListView
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from pyexpat.errors import messages
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from .models import *
from django.http import JsonResponse
from django.views import View
from .forms import *
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
import datetime
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.db.models import Prefetch
from django.contrib.auth import logout

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home:home')  # Redirect to home:home after successful login
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home:home')  # Redirect to home page after logout

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home:home')  # Redirect to home:home after successful registration and login
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

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

        if 'username' in request.POST:
            # Share folder functionality
            username = request.POST.get('username')
            folder_to_share = Folder.objects.get(id=request.POST.get('folder_id'))  # Get the folder to share
            
            try:
                invited_user = User.objects.get(username=username)
                FolderInvitation.objects.create(folder=folder_to_share, invited_user=invited_user, sender=request.user)
                folder_to_share.users_with_access.add(invited_user)
                messages.success(request, f"Folder '{folder_to_share.name}' shared with {username}.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        
        else:
            # Create subfolder functionality
            form = FolderForm(request.POST)
            if form.is_valid():
                new_folder = form.save(commit=False)
                new_folder.owner = request.user
                new_folder.parent = folder  # Set the parent folder
                new_folder.save()

        # After sharing a folder, fetch updated data and render the same page
        files = folder.files.all()
        subfolders = folder.children.all()
        form = FolderForm()  # Reset the form

        return render(
            request,
            "home/folder_detail.html",
            {"folder": folder, "files": files, "subfolders": subfolders, "form": form},
        )




@method_decorator(login_required, name='dispatch')
class SharedContentView(View):
    def get(self, request):
        user = request.user
        
        # Get folders the user has been invited to
        invited_folders = Folder.objects.filter(invitations__invited_user=user).distinct()
        
        # Get files the user has been invited to
        invited_files = File.objects.filter(fileinvitation__invited_user=user).distinct()  # Use the related name correctly
        
        return render(request, "home/shared_content.html", {
            "invited_folders": invited_folders,
            "invited_files": invited_files,
        })


        
class SharePersonalFolder(View):
    def post(self, request, *args, **kwargs):
        folder_id = request.POST.get('folder_id')
        folder = get_object_or_404(Folder, pk=folder_id)
        username = request.POST.get('username')
        
        try:
            invited_user = User.objects.get(username=username)
            # Create the folder invitation
            FolderInvitation.objects.create(
                folder=folder,
                invited_user=invited_user,
                sender=request.user
            )
            # Optionally add the invited user to folder's access list
            folder.users_with_access.add(invited_user)
            messages.success(request, f"Folder shared with {username}.")  # Correct usage
        except User.DoesNotExist:
            messages.error(request, "User not found.")  # Correct usage
        
        # Redirect back to the folder list
        return redirect('home:my_folders')

class AddFolderView(View):
    def post(self, request):
        if request.user.is_authenticated:
            folder_name = request.POST.get('folder_name')
            if folder_name:
                Folder.objects.create(name=folder_name, owner=request.user)  # Adjust as per your model structure
                return redirect('home:my_folders')  # Redirect back to the folders page
        return HttpResponse("Unauthorized", status=401)  # Or handle accordingly
    
class MyFoldersView(View):
    def get(self, request):
        if request.user.is_authenticated:
            # Get the user's folders without a parent
            my_folders = Folder.objects.filter(owner=request.user, parent=None)
            return render(request, 'home/my_folders.html', {'my_folders': my_folders})
        else:
            return redirect('login')  # Redirect unauthenticated users

class ShareFolderView(View):
    def post(self, request, folder_id):
        # Get the folder to share
        folder = get_object_or_404(Folder, pk=folder_id)

        # Get the username from the request
        username = request.POST.get('username')

        try:
            # Find the user to share the folder with
            user_to_share = User.objects.get(username=username)

            # Check if the user already has access
            if user_to_share in folder.users_with_access.all():
                messages.warning(request, f"{username} already has access to this folder.")
            else:
                # Add the user to the folder's access list
                folder.users_with_access.add(user_to_share)
                messages.success(request, f"Folder shared with {username} successfully!")
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' does not exist.")

        return redirect('home:folder_detail', pk=folder.pk)  # Redirect to folder detail page
    

class DeleteFolderView(View):
    def post(self, request, folder_id):
        if request.user.is_authenticated:
            folder = get_object_or_404(Folder, pk=folder_id, owner=request.user)
            parent_folder_id = folder.parent.id if folder.parent else None  # Get the parent folder ID
            folder.delete()
            # Redirect back to the parent folder's detail view or my_folders if no parent
            return redirect('home:folder_detail', folder_id=parent_folder_id) if parent_folder_id else redirect('home:my_folders')
        return redirect('login')  # Redirect unauthenticated users


def delete_file(request, file_id):
    file = get_object_or_404(File, pk=file_id)
    file.delete()  # Delete the file
    messages.success(request, "File deleted successfully.")  # Show success message
    return redirect(request.META.get('HTTP_REFERER', 'home:my_folders'))  # Redirect back


class ShareFileView(View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id)  # Get the file to share
        username = request.POST.get('username')  # Get the username from the form

        try:
            invited_user = User.objects.get(username=username)  # Check if user exists
            # Create the file invitation (You may need to adjust this based on your model)
            FileInvitation.objects.create(file=file, invited_user=invited_user, sender=request.user)
            messages.success(request, f"File '{file.name}' shared with {username}.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

        # Redirect back to the referring page (can be customized)
        return redirect(request.META.get('HTTP_REFERER', 'home:my_folders'))
    
    
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
        

@method_decorator(login_required, name='dispatch')
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
    
    
class TeamFolderListView(LoginRequiredMixin, FormMixin, ListView):
    model = TeamFolder
    template_name = 'home/team_folders.html'
    context_object_name = 'team_folders'
    form_class = PermissionForm

    def get_queryset(self):
        owned_folders = TeamFolder.objects.filter(owner=self.request.user)
        invited_folders = TeamFolder.objects.filter(users_with_access=self.request.user)

        return (owned_folders | invited_folders).distinct().prefetch_related(
            Prefetch(
                'permissions',
                queryset=TeamFolderPermission.objects.all(),
                to_attr='user_permissions'
            ),
            'users_with_access'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add_team_folder'] = (
            self.request.user.is_superuser or 
            self.request.user.has_perm('home.admin_permission')
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            permission_instance = get_object_or_404(TeamFolderPermission, id=request.POST['permission_id'])
            permission_instance.can_edit = form.cleaned_data['can_edit']
            permission_instance.can_delete = form.cleaned_data['can_delete']
            permission_instance.can_create = form.cleaned_data['can_create']
            permission_instance.can_share = form.cleaned_data['can_share']
            permission_instance.can_manage = form.cleaned_data['can_manage']
            permission_instance.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

class EditPermissionView(LoginRequiredMixin, View):
    def post(self, request, folder_id, member_id):
        # Get the folder and member objects
        folder = get_object_or_404(TeamFolder, id=folder_id)
        member = get_object_or_404(User, id=member_id)
        
        # Check if the user is allowed to edit permissions
        if not request.user == folder.owner:  # You can customize this check
            messages.error(request, "You do not have permission to edit permissions.")
            return redirect('team_folders')

        # Update permissions based on the form data
        can_edit = request.POST.get('can_edit') == 'on'
        can_delete = request.POST.get('can_delete') == 'on'
        can_create = request.POST.get('can_create') == 'on'
        can_share = request.POST.get('can_share') == 'on'
        can_manage = request.POST.get('can_manage') == 'on'

        # Update or create the permission object
        permission, created = TeamFolderPermission.objects.update_or_create(
            user=member,
            team_folder=folder,
            defaults={
                'can_edit': can_edit,
                'can_delete': can_delete,
                'can_create': can_create,
                'can_share': can_share,
                'can_manage': can_manage,
            }
        )

        messages.success(request, f"Permissions for {member.username} updated successfully.")
        return redirect('team_folders')  # Redirect to the appropriate page
    
class TeamFolderDetailView(View):
    def get(self, request, id):
        # Get the specific TeamFolder instance
        folder = get_object_or_404(TeamFolder, id=id)
        
        # Retrieve files associated with this TeamFolder
        files = TeamFolderFile.objects.filter(team_folder=folder)  # Ensure you query TeamFolderFile
        
        # No subfolders in TeamFolder as per your model design
        subfolders = []  # or however you want to handle this
        
        return render(request, 'home/team_folder_detail.html', {
            'folder': folder,
            'files': files,
            'subfolders': subfolders,
        })
        
        
class TeamFolderCreateView(View):
    def get(self, request):
        form = TeamFolderForm()
        return render(request, 'home/team_folders.html', {'form': form})

    def post(self, request):
        form = TeamFolderForm(request.POST)
        if form.is_valid():
            team_folder = form.save(commit=False)
            team_folder.owner = request.user  # Set the owner to the current user
            team_folder.save()
            return redirect('home:team_folders')  # Redirect to the team folders list view
        # If form is invalid, render the form again with errors
        return render(request, 'home/team_folders.html', {'form': form})

class TeamFolderUpdateView(LoginRequiredMixin, UpdateView):
    model = TeamFolder
    form_class = TeamFolderForm  # Reuse the same form for updating
    template_name = 'home/team_folder_form.html'  # Template for editing team folders
    success_url = reverse_lazy('home:team_folder_list')  # Redirect after update

    def get_queryset(self):
        # Ensure that users can only update their own folders
        return TeamFolder.objects.filter(owner=self.request.user)

class TeamFolderDeleteView(LoginRequiredMixin, DeleteView):
    model = TeamFolder
    success_url = reverse_lazy('home:team_folders')  # Redirect after deletion

    def get_queryset(self):
        # Ensure that users can only delete their own folders
        return TeamFolder.objects.filter(owner=self.request.user)

# views.py
class AddMemberToTeamFolderView(View):
    def post(self, request, pk):
        folder = get_object_or_404(TeamFolder, pk=pk)
        username = request.POST.get('username')
        can_share = request.POST.get('can_share') == 'on'
        can_create = request.POST.get('can_create') == 'on'
        can_edit = request.POST.get('can_edit') == 'on'
        can_delete = request.POST.get('can_delete') == 'on'

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Handle user not found
            return redirect('home:team_folder_detail', id=pk)  # Change 'pk' to 'id' here

        permission, created = TeamFolderPermission.objects.get_or_create(
            team_folder=folder,
            user=user,
            defaults={
                'can_share': can_share,
                'can_create': can_create,
                'can_edit': can_edit,
                'can_delete': can_delete,
            }
        )

        if not created:
            permission.can_share = can_share
            permission.can_create = can_create
            permission.can_edit = can_edit
            permission.can_delete = can_delete
            permission.save()

        return redirect('home:team_folder_detail', id=pk)  # Change 'pk' to 'id' here
