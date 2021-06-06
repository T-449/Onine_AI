from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# Create your views here.
from users.forms import UserRegisterForm, UserUpdateForm, UserProfileUpdateForm
from game_creator.models import GameCreatorWorkspaceACL, Game


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    context = {'form': form}
    return render(request, 'users/register.html', context)


def view_profile(request, profile_name):
    workspaces = GameCreatorWorkspaceACL.objects.filter(user=request.user)
    # print(request.user,type(request.user))
    profile_user = get_object_or_404(User, username=profile_name)
    context = {
        'profile_user': profile_user,
        'workspaces' : workspaces
    }
    return render(request, 'users/profile.html', context)

def homepage(request):
    if (request.user.is_authenticated):
        return redirect('viewprofile', profile_name=request.user.username)
    else:
        return redirect('login')

@login_required
def update_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        up_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)

        if (u_form.is_valid() and up_form.is_valid()):
            u_form.save()
            up_form.save()
            messages.success(request, f'Your profile has been updated.')
            return redirect('viewprofile', profile_name=request.user.username)

    else:
        u_form = UserUpdateForm(instance=request.user)
        up_form = UserProfileUpdateForm(instance=request.user.userprofile)
    # print(request.user,type(request.user))

    context = {
        'u_form': u_form,
        'up_form': up_form
    }

    return render(request, 'users/update_profile.html', context)

@login_required
def create_game(request):
    game = Game.objects.create_game(request.user)
    return redirect('game_creator_show_workspace', workspace_id=game.game_uuid)
