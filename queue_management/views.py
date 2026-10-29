from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.models import User
from audit.models import AuditLog
from notifications.models import Notification
from patients.models import Patient
from .forms import QueueEntryForm
from .models import QueueEntry


@login_required
@require_http_methods(['GET', 'POST'])
def dashboard(request):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
        raise PermissionDenied('You do not have access to the queue.')

    form = QueueEntryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient = form.cleaned_data['patient']
        if QueueEntry.objects.filter(
            patient=patient,
            queue_date=date.today(),
            status__in=[QueueEntry.WAITING, QueueEntry.CALLED, QueueEntry.IN_CONSULTATION],
        ).exists():
            messages.error(request, 'This patient already has an active queue entry for today.')
            return redirect('dashboard')

        queue_entry = form.save(commit=False)
        queue_entry.created_by = request.user
        queue_entry.queue_date = date.today()
        queue_entry.status = QueueEntry.WAITING
        queue_entry.ticket_number = f'Q-{date.today().strftime("%Y%m%d")}-{timezone.now().strftime("%H%M%S")}-{patient.patient_id[-4:]}'
        queue_entry.save()
        AuditLog.objects.create(
            user=request.user,
            action='QUEUE_ENTRY_CREATED',
            queue_entry=queue_entry,
            description=f'Added {queue_entry.patient.full_name} to the queue.',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} joined the waiting queue.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, f'Added {queue_entry.patient.full_name} to the queue with ticket {queue_entry.ticket_number}.')
        return redirect('dashboard')

    entries = QueueEntry.objects.filter(queue_date=date.today()).select_related('patient', 'assigned_doctor').order_by('registered_at')
    summary = {
        'total_registered_today': Patient.objects.filter(registered_at__date=date.today()).count(),
        'waiting': entries.filter(status=QueueEntry.WAITING).count(),
        'called': entries.filter(status=QueueEntry.CALLED).count(),
        'in_consultation': entries.filter(status=QueueEntry.IN_CONSULTATION).count(),
        'completed': entries.filter(status=QueueEntry.COMPLETED).count(),
        'no_show': entries.filter(status=QueueEntry.NO_SHOW).count(),
    }
    consultation = entries.filter(status=QueueEntry.IN_CONSULTATION).order_by('consultation_started_at').first()
    recent_activity = AuditLog.objects.select_related('user', 'queue_entry').order_by('-created_at')[:8]
    appointments = entries.order_by('registered_at')[:4]
    return render(
        request,
        'queue_management/queue_dashboard.html',
        {'entries': entries, 'appointments': appointments, 'current_consultation': consultation, 'summary': summary, 'recent_activity': recent_activity, 'form': form},
    )


@login_required
@require_http_methods(['POST'])
def call_next_patient(request):
    if request.user.role not in [User.ADMIN, User.DOCTOR]:
        raise PermissionDenied('Only doctors and administrators can call the next patient.')

    with transaction.atomic():
        waiting = QueueEntry.objects.filter(queue_date=date.today(), status=QueueEntry.WAITING).select_related('patient').order_by('registered_at', 'id')
        queue_entry = waiting.first()
        if not queue_entry:
            messages.info(request, 'There are no waiting patients to call.')
            return redirect('dashboard')

        queue_entry.status = QueueEntry.CALLED
        queue_entry.called_at = timezone.now()
        queue_entry.save(update_fields=['status', 'called_at'])
        AuditLog.objects.create(
            user=request.user,
            action='PATIENT_CALLED',
            queue_entry=queue_entry,
            description=f'Called {queue_entry.patient.full_name} ({queue_entry.ticket_number}).',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} was called.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, f'{queue_entry.patient.full_name} was called.')
    return redirect('dashboard')


@login_required
@require_http_methods(['POST'])
def queue_entry_action(request, pk):
    queue_entry = get_object_or_404(QueueEntry, pk=pk)
    action = request.POST.get('action')

    if request.user.role not in [User.ADMIN, User.DOCTOR, User.RECEPTIONIST]:
        raise PermissionDenied('You cannot change queue status.')

    if action == 'start_consultation':
        if request.user.role not in [User.ADMIN, User.DOCTOR]:
            raise PermissionDenied('Only doctors can start consultations.')
        if queue_entry.status not in [QueueEntry.CALLED, QueueEntry.WAITING]:
            messages.error(request, 'Only a called patient can start consultation.')
            return redirect('dashboard')
        queue_entry.status = QueueEntry.IN_CONSULTATION
        queue_entry.consultation_started_at = timezone.now()
        queue_entry.save(update_fields=['status', 'consultation_started_at'])
        AuditLog.objects.create(
            user=request.user,
            action='CONSULTATION_STARTED',
            queue_entry=queue_entry,
            description=f'{queue_entry.patient.full_name} started consultation.',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} entered consultation.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, 'Consultation started.')
    elif action == 'complete_consultation':
        if request.user.role not in [User.ADMIN, User.DOCTOR]:
            raise PermissionDenied('Only doctors can complete consultations.')
        if queue_entry.status != QueueEntry.IN_CONSULTATION:
            messages.error(request, 'Only a patient in consultation can complete it.')
            return redirect('dashboard')
        queue_entry.status = QueueEntry.COMPLETED
        queue_entry.completion_time = timezone.now()
        queue_entry.save(update_fields=['status', 'completion_time'])
        AuditLog.objects.create(
            user=request.user,
            action='CONSULTATION_COMPLETED',
            queue_entry=queue_entry,
            description=f'{queue_entry.patient.full_name} completed consultation.',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} completed consultation.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, 'Consultation completed.')
    elif action == 'mark_no_show':
        if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
            raise PermissionDenied('You cannot mark a patient as a no-show.')
        if queue_entry.status not in [QueueEntry.CALLED, QueueEntry.WAITING]:
            messages.error(request, 'This queue status cannot be marked as no-show.')
            return redirect('dashboard')
        queue_entry.status = QueueEntry.NO_SHOW
        queue_entry.no_show_at = timezone.now()
        queue_entry.save(update_fields=['status', 'no_show_at'])
        AuditLog.objects.create(
            user=request.user,
            action='NO_SHOW',
            queue_entry=queue_entry,
            description=f'{queue_entry.patient.full_name} was marked as no-show.',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} was marked as no-show.',
            notification_type='alert',
            related_queue_entry=queue_entry,
        )
        messages.warning(request, 'No-show recorded.')
    elif action == 'cancel':
        if request.user.role not in [User.ADMIN, User.RECEPTIONIST]:
            raise PermissionDenied('You cannot cancel queue entries.')
        if queue_entry.status in [QueueEntry.COMPLETED, QueueEntry.NO_SHOW, QueueEntry.CANCELLED]:
            messages.error(request, 'This queue entry cannot be cancelled in its current state.')
            return redirect('dashboard')
        queue_entry.status = QueueEntry.CANCELLED
        queue_entry.cancelled_at = timezone.now()
        queue_entry.save(update_fields=['status', 'cancelled_at'])
        AuditLog.objects.create(
            user=request.user,
            action='QUEUE_CANCELLED',
            queue_entry=queue_entry,
            description=f'Cancelled {queue_entry.ticket_number} for {queue_entry.patient.full_name}.',
        )
        Notification.create_for_all(
            f'{queue_entry.ticket_number} was cancelled.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, 'Queue entry cancelled.')
    elif action == 'requeue':
        if request.user.role not in [User.ADMIN, User.RECEPTIONIST]:
            raise PermissionDenied('You cannot requeue patients.')
        if queue_entry.status != QueueEntry.CANCELLED:
            messages.error(request, 'Only a cancelled queue entry can be returned to the waiting list.')
            return redirect('dashboard')
        queue_entry.status = QueueEntry.WAITING
        queue_entry.cancelled_at = None
        queue_entry.save(update_fields=['status', 'cancelled_at'])
        AuditLog.objects.create(
            user=request.user,
            action='REQUEUED',
            queue_entry=queue_entry,
            description=f'{queue_entry.patient.full_name} was moved back to the waiting queue.',
        )
        Notification.create_for_all(
            f'{queue_entry.patient.full_name} re-entered the waiting queue.',
            notification_type='queue_update',
            related_queue_entry=queue_entry,
        )
        messages.success(request, 'Patient returned to the waiting queue.')
    else:
        messages.error(request, 'Unsupported queue action.')
        return redirect('dashboard')
    return redirect('dashboard')


@login_required
@require_http_methods(['GET'])
def queue_history(request):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
        raise PermissionDenied('You do not have access to the queue history.')

    entries = QueueEntry.objects.select_related('patient', 'assigned_doctor').all().order_by('-registered_at')
    queue_date = request.GET.get('queue_date')
    status = request.GET.get('status')
    patient_name = request.GET.get('patient_name', '').strip()

    if queue_date:
        entries = entries.filter(queue_date=queue_date)
    if status:
        entries = entries.filter(status=status)
    if patient_name:
        entries = entries.filter(patient__full_name__icontains=patient_name)
    return render(
        request,
        'queue_management/history.html',
        {'entries': entries, 'queue_date': queue_date, 'status': status, 'patient_name': patient_name, 'status_choices': QueueEntry.STATUS_CHOICES},
    )
