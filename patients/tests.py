from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from patients.models import Patient


class PatientTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reception', password='secret123', role=User.RECEPTIONIST)
        self.client.login(username='reception', password='secret123')

    def test_register_patient(self):
        response = self.client.post(reverse('patient_register'), {
            'full_name': 'Jane Doe',
            'date_of_birth': '1990-01-15',
            'sex': 'Female',
            'phone_number': '+123456789',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Patient.objects.filter(full_name='Jane Doe').exists())

    def test_patient_search(self):
        Patient.objects.create(patient_id='PT-ABC123', full_name='Alice Example', phone_number='123')
        response = self.client.get(reverse('patient_search'), {'q': 'Alice'})
        self.assertContains(response, 'Alice Example')

    def test_receptionist_can_update_patient(self):
        patient = Patient.objects.create(
            patient_id='PT-ABC123',
            full_name='Alice Example',
            phone_number='123',
        )

        response = self.client.post(reverse('patient_update', args=[patient.pk]), {
            'full_name': 'Alice Updated',
            'date_of_birth': '1990-01-15',
            'sex': 'Female',
            'phone_number': '456',
        })

        self.assertRedirects(response, reverse('patient_detail', args=[patient.pk]))
        patient.refresh_from_db()
        self.assertEqual(patient.full_name, 'Alice Updated')
        self.assertEqual(patient.phone_number, '456')
        self.assertEqual(patient.patient_id, 'PT-ABC123')

    def test_doctor_cannot_update_patient(self):
        patient = Patient.objects.create(patient_id='PT-ABC123', full_name='Alice Example')
        self.user.role = User.DOCTOR
        self.user.save()

        response = self.client.get(reverse('patient_update', args=[patient.pk]))

        self.assertEqual(response.status_code, 403)
