from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from accounts.models import User
from .models import AuditLog


@login_required
def audit_log_view(request):
    if request.user.role != User.ADMIN:
        raise PermissionDenied('Only administrators can review audit logs.')
    logs = AuditLog.objects.select_related('user', 'queue_entry').order_by('-created_at')[:50]
    return render(request, 'audit/audit_log.html', {'logs': logs})
