import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import User
from queue_management.models import QueueEntry
from .forms import PatientRegistrationForm
from .models import Patient


@login_required
@require_http_methods(['GET', 'POST'])
def register_patient(request):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST]:
        raise PermissionDenied('You are not allowed to register patients.')

    form = PatientRegistrationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        patient = form.save(commit=False)
        patient.created_by = request.user
        patient.patient_id = f'PT-{uuid.uuid4().hex[:8].upper()}'
        patient.save()
        messages.success(request, f'Patient {patient.full_name} was registered with ID {patient.patient_id}.')
        return redirect('patient_search')
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Register patient'})


@login_required
@require_http_methods(['GET', 'POST'])
def update_patient(request, pk):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST]:
        raise PermissionDenied('You are not allowed to update patient records.')

    patient = get_object_or_404(Patient, pk=pk)
    form = PatientRegistrationForm(
        request.POST if request.method == 'POST' else None,
        instance=patient,
    )
    if request.method == 'POST' and form.is_valid():
        patient = form.save()
        messages.success(request, f'Patient {patient.full_name} was updated.')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Update patient'})


@login_required
@require_http_methods(['GET'])
def patient_detail(request, pk):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
        raise PermissionDenied('You are not allowed to view patient details.')

    patient = get_object_or_404(Patient, pk=pk)
    entries = QueueEntry.objects.filter(patient=patient).select_related('assigned_doctor').order_by('-registered_at')
    return render(request, 'patients/patient_detail.html', {'patient': patient, 'entries': entries})


@login_required
@require_http_methods(['GET'])
def patient_search(request):
    if request.user.role not in [User.ADMIN, User.RECEPTIONIST, User.DOCTOR]:
        raise PermissionDenied('You are not allowed to search patients.')

    query = request.GET.get('q', '').strip()
    patients = Patient.objects.all().order_by('-registered_at')
    if query:
        patients = patients.filter(Q(full_name__icontains=query) | Q(patient_id__icontains=query))
    return render(request, 'patients/search.html', {'patients': patients, 'query': query})
