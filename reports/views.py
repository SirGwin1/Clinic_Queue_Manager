import csv
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from patients.models import Patient
from queue_management.models import QueueEntry


@login_required
def reports_view(request):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
        raise PermissionDenied('You cannot access reports.')

    selected_day = request.GET.get('date', date.today().isoformat())
    report_date = timezone.datetime.strptime(selected_day, '%Y-%m-%d').date() if selected_day else date.today()
    entries = QueueEntry.objects.filter(queue_date=report_date)

    registered_today = Patient.objects.filter(registered_at__date=report_date).count()
    waiting_count = entries.filter(status=QueueEntry.WAITING).count()
    completed_consultations = entries.filter(status=QueueEntry.COMPLETED).count()
    no_show_count = entries.filter(status=QueueEntry.NO_SHOW).count()

    wait_minutes = []
    for item in entries.filter(called_at__isnull=False):
        if item.called_at and item.registered_at:
            wait_minutes.append((item.called_at - item.registered_at).total_seconds() / 60)
    avg_waiting = round(sum(wait_minutes) / len(wait_minutes), 1) if wait_minutes else 0

    consultation_durations = []
    for item in entries.filter(status=QueueEntry.COMPLETED, consultation_started_at__isnull=False, completion_time__isnull=False):
        if item.consultation_started_at and item.completion_time:
            consultation_durations.append((item.completion_time - item.consultation_started_at).total_seconds() / 60)
    avg_consultation = round(sum(consultation_durations) / len(consultation_durations), 1) if consultation_durations else 0

    per_day = Patient.objects.filter(registered_at__date=report_date).values('registered_at__date').annotate(count=Count('id')).order_by('registered_at__date')

    context = {
        'selected_day': selected_day,
        'registered_per_day': per_day,
        'completed_consultations': completed_consultations,
        'waiting_count': waiting_count,
        'no_show_count': no_show_count,
        'avg_waiting_minutes': avg_waiting,
        'avg_consultation_minutes': avg_consultation,
        'registered_today': registered_today,
    }
    return render(request, 'reports/reports.html', context)


@login_required
def export_report_csv(request):
    if request.user.role != User.ADMIN:
        raise PermissionDenied('Only administrators can export reports.')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clinic_queue_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Patients registered', 'Waiting', 'Completed', 'No-show'])
    today = date.today()
    writer.writerow([
        today,
        Patient.objects.filter(registered_at__date=today).count(),
        QueueEntry.objects.filter(queue_date=today, status=QueueEntry.WAITING).count(),
        QueueEntry.objects.filter(queue_date=today, status=QueueEntry.COMPLETED).count(),
        QueueEntry.objects.filter(queue_date=today, status=QueueEntry.NO_SHOW).count(),
    ])
    return response
