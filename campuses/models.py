# web/campuses/models.py
from django.db import models

class Plantel(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(blank=True, null=True)
    
    nivel_educativo = models.CharField(
        max_length=50, 
        choices=[('BASICA', 'Básica (Sec/Prepa)'), ('SUPERIOR', 'Superior (Universidad)')],
        default='BASICA'
    )
    color_tema = models.CharField(max_length=20, default='blue')
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_aulas = models.PositiveIntegerField(default=20, verbose_name="Capacidad de Aulas")

    def __str__(self):
        return self.nombre