from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Súper Admin'),
        ('DIRECTOR', 'Director'),
        ('COORD', 'Coordinador'),
        ('DOCENTE', 'Docente'),
        ('ALUMNO', 'Alumno'),
        ('TUTOR', 'Padre/Tutor'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='ALUMNO')
    plantel_id = models.IntegerField(null=True, blank=True) # ID del plantel de Supabase

    def __str__(self):
        return f"{self.username} - {self.rol}"