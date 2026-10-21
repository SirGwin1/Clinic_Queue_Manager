
from django import forms
from .models import Registration


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["name", "phone", "reasons"]

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter your name"
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Enter phone number"
            }),
            "reasons": forms.Textarea(attrs={
                "placeholder": "Enter your reason for visiting"
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"]

        allowed_characters = phone.replace("+", "", 1)

        if not allowed_characters.replace(" ", "").replace("-", "").isdigit():
            raise forms.ValidationError(
                "Enter a valid phone number using digits, spaces, "
                "hyphens, or a leading plus sign."
            )

        return phone
