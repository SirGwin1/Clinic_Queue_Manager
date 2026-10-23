from django import forms
from accounts.models import User
from patients.models import Patient
from .models import QueueEntry


class QueueEntryForm(forms.ModelForm):
    class Meta:
        model = QueueEntry
        fields = ['patient', 'assigned_doctor']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'assigned_doctor': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = Patient.objects.order_by('full_name')
        self.fields['assigned_doctor'].queryset = User.objects.filter(role=User.DOCTOR).order_by('username')
        self.fields['assigned_doctor'].required = False
