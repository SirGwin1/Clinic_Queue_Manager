from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='secret123', role=User.ADMIN)

    def test_valid_login(self):
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'secret123'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_invalid_login(self):
        response = self.client.post(reverse('login'), {'username': 'admin', 'password': 'wrong-pass'})
        self.assertContains(response, 'Invalid username or password.')

    def test_protected_pages_require_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_role_access_control(self):
        doctor = User.objects.create_user(username='doctor', password='secret123', role=User.DOCTOR)
        self.client.login(username='doctor', password='secret123')
        response = self.client.get(reverse('user_management'))
        self.assertEqual(response.status_code, 403)
