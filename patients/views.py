from django.shortcuts import render

# Create your views here.
def user_registration(request):
    if request.method == "GET":
        return render(request, "patients/registration.html")