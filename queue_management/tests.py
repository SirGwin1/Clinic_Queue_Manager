from datetime import date
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from patients.models import Patient
from queue_management.models import QueueEntry


class QueueTests(TestCase):
    def setUp(self):
        self.reception = User.objects.create_user(username='reception', password='secret123', role=User.RECEPTIONIST)
        self.doctor = User.objects.create_user(username='doctor', password='secret123', role=User.DOCTOR)
        self.patient_a = Patient.objects.create(patient_id='PT-A1', full_name='Patient A')
        self.patient_b = Patient.objects.create(patient_id='PT-B2', full_name='Patient B')

    def test_queue_entry_creation_and_call_next(self):
        self.client.login(username='reception', password='secret123')
        response = self.client.post(reverse('dashboard'), {'patient': self.patient_a.pk})
        self.assertEqual(response.status_code, 302)
        self.client.logout()
        self.client.login(username='doctor', password='secret123')
        response = self.client.post(reverse('call_next_patient'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(QueueEntry.objects.filter(patient=self.patient_a, status=QueueEntry.CALLED).count(), 1)

    def test_invalid_status_transition(self):
        entry = QueueEntry.objects.create(patient=self.patient_a, ticket_number='Q-TEST-1', queue_date=date.today(), status=QueueEntry.WAITING)
        self.client.login(username='doctor', password='secret123')
        response = self.client.post(reverse('queue_entry_action', args=[entry.pk]), {'action': 'complete_consultation'})
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.status, QueueEntry.WAITING)

    def test_mark_no_show(self):
        entry = QueueEntry.objects.create(patient=self.patient_b, ticket_number='Q-TEST-2', queue_date=date.today(), status=QueueEntry.CALLED)
        self.client.login(username='reception', password='secret123')
        response = self.client.post(reverse('queue_entry_action', args=[entry.pk]), {'action': 'mark_no_show'})
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.status, QueueEntry.NO_SHOW)

    def test_queue_history_date_filter_renders_blank_by_default(self):
        self.client.login(username='reception', password='secret123')
        response = self.client.get(reverse('queue_history'))
        self.assertContains(response, 'name="queue_date" class="form-control" value=""')

    def test_dashboard_uses_real_todays_appointments(self):
        QueueEntry.objects.create(patient=self.patient_a, ticket_number='Q-T1', queue_date=date.today(), status=QueueEntry.WAITING)
        QueueEntry.objects.create(patient=self.patient_b, ticket_number='Q-T2', queue_date=date.today(), status=QueueEntry.CALLED)
        self.client.login(username='reception', password='secret123')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, self.patient_a.full_name)
        self.assertContains(response, self.patient_b.full_name)
        self.assertNotContains(response, 'Sarah Williams')
