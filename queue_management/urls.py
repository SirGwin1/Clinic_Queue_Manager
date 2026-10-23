from django.urls import path
from .views import call_next_patient, dashboard, queue_entry_action, queue_history

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('history/', queue_history, name='queue_history'),
    path('call-next/', call_next_patient, name='call_next_patient'),
    path('<int:pk>/action/', queue_entry_action, name='queue_entry_action'),
]
