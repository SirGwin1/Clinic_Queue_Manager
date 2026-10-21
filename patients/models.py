from django.db import models

from django.db import models

class Registration(models.Model):
    name = models.CharField(max_length=64)
    phone = models.CharField(max_length=13)
    reasons = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.phone} - {self.reasons}"