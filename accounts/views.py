from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import StaffAuthenticationForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = StaffAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        pw = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=pw)
        if user is not None and user.is_active:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
@require_http_methods(['GET', 'POST'])
def user_management(request):
    if request.user.role != User.ADMIN:
        raise PermissionDenied('You do not have permission to manage users.')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        pw = request.POST.get('password', '')
        role = request.POST.get('role', User.RECEPTIONIST)
        if not username or not pw:
            messages.error(request, 'Username and password are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'A user with that username already exists.')
        else:
            user = User.objects.create_user(username=username, password=pw, role=role)
            messages.success(request, f'Created staff account for {user.username}.')

    users = User.objects.order_by('username')
    return render(request, 'accounts/user_management.html', {'users': users})
