# web/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from campuses.models import Plantel 

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Súper Admin'),
        ('DIRECTOR', 'Director'),
        ('COORD', 'Coordinador'),
        ('DOCENTE', 'Docente'),
        ('ALUMNO', 'Alumno'),
        ('TUTOR', 'Padre/Tutor'),
    )
    
    
    plantel = models.ForeignKey(
        Plantel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuarios'
    )
    alumno_grupo = models.ForeignKey(
        'academic.Grupo', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='alumnos'
    )
    ESTATUS_ALUMNO = [
        ('ACTIVO', 'Activo'),
        ('PENDIENTE', 'Pendiente de Documentos'),
        ('BAJA', 'Baja Temporal'),
    ]
    estatus = models.CharField(max_length=20, choices=ESTATUS_ALUMNO, default='ACTIVO')
    rol = models.CharField(max_length=20, choices=ROLES, default='ALUMNO')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    status = models.BooleanField(default=True)
    direccion = models.TextField(blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
    
class Tutor(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tutores")
    nombre = models.CharField(max_length=100)
    parentesco = models.CharField(max_length=50)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.alumno.nombre}"