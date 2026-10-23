from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    if request.method == 'POST':
        ids = request.POST.getlist('notification_ids')
        Notification.objects.filter(user=request.user, id__in=ids).update(is_read=True)
        messages.success(request, 'Notifications marked as read.')
        return redirect('notification_center')

    return render(request, 'notifications/notification_center.html', {'notifications': notifications, 'unread_count': unread_count})


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return JsonResponse({'status': 'ok'})
