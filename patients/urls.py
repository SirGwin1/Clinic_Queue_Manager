from django.urls import path
from .views import patient_detail, patient_search, register_patient, update_patient

urlpatterns = [
    path('register/', register_patient, name='patient_register'),
    path('search/', patient_search, name='patient_search'),
    path('<int:pk>/edit/', update_patient, name='patient_update'),
    path('<int:pk>/', patient_detail, name='patient_detail'),
]
