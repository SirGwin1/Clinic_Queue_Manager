from django import forms
from .models import Patient


class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'date_of_birth', 'sex', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'sex': forms.Select(
                attrs={'class': 'form-select'},
                choices=[('', 'Select sex'), ('Female', 'Female'), ('Male', 'Male'), ('Other', 'Other')],
            ),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+27 000 000 000'}),
        }

    def clean_full_name(self):
        name = (self.cleaned_data.get('full_name') or '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Provide the patient full name.')
        return name
