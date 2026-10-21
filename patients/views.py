
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm


def user_registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            patient = form.save()

            messages.success(
                request,
                f"Registration successful! Welcome, {patient.name}. "
                "Your information has been saved."
            )

            return render(request, "patients/success_message.html")


    else:
        form = RegistrationForm()

    return render(
        request,
        "patients/registration.html",
        {"form": form}
    )


