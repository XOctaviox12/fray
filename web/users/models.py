# web/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from campuses.models import Plantel


class User(AbstractUser):
    ROLES = (
        ('ADMIN',     'Súper Admin'),
        ('DIRECTOR',  'Director'),
        ('COORD',     'Coordinador'),
        ('DOCENTE',   'Docente'),
        ('ALUMNO',    'Alumno'),
        ('TUTOR',     'Padre/Tutor'),
    )

    plantel = models.ForeignKey(
        Plantel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuarios',
    )

    # ── Solo para alumnos ──────────────────────────────────────────────────
    alumno_grupo = models.ForeignKey(
        'academic.Grupo',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alumnos',
    )
    ESTATUS_ALUMNO = [
        ('ACTIVO',    'Activo'),
        ('PENDIENTE', 'Pendiente de Documentos'),
        ('BAJA',      'Baja Temporal'),
    ]
    estatus = models.CharField(max_length=20, choices=ESTATUS_ALUMNO, default='ACTIVO')

    # ── Campos comunes ────────────────────────────────────────────────────
    rol              = models.CharField(max_length=20, choices=ROLES, default='ALUMNO')
    telefono         = models.CharField(max_length=15,  blank=True, null=True)
    direccion        = models.TextField(blank=True, null=True)
    foto_perfil      = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    password_plana   = models.CharField(max_length=50, blank=True, null=True)

    # ── Helpers de rol ────────────────────────────────────────────────────
    @property
    def es_docente(self):
        return self.rol == 'DOCENTE'

    @property
    def es_director(self):
        return self.rol in ('DIRECTOR', 'ADMIN')

    @property
    def es_coordinador(self):
        return self.rol == 'COORD'

    @property
    def grupos_docente(self):
        """Devuelve los grupos asignados al docente (a través de DocenteGrupo)."""
        if not self.es_docente:
            return []
        return [dg.grupo for dg in self.asignaciones_grupo.select_related('grupo').all()]

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"


class Tutor(models.Model):
    alumno     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutores')
    nombre     = models.CharField(max_length=100)
    parentesco = models.CharField(max_length=50)
    telefono   = models.CharField(max_length=20)
    correo     = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.alumno.get_full_name()}"


class DocenteGrupo(models.Model):
    """
    Relación M2M enriquecida entre un Docente y un Grupo.
    Permite saber qué materia imparte el docente en ese grupo
    y en qué ciclo escolar está activa la asignación.
    """
    docente    = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='asignaciones_grupo',
    )
    grupo      = models.ForeignKey(
        'academic.Grupo',
        on_delete=models.CASCADE,
        related_name='docentes_asignados',
    )
    asignatura = models.ForeignKey(
        'academic.Asignatura',
        on_delete=models.CASCADE,
        related_name='docentes_grupo',
        null=True, blank=True,   # null si un docente es tutor del grupo sin materia específica
    )
    ciclo      = models.CharField(
        max_length=20,
        default='2026-1',
        help_text='Ejemplo: 2026-1 para Ene-Abr 2026',
    )
    activo     = models.BooleanField(default=True)
    fecha_asignacion = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('docente', 'grupo', 'asignatura', 'ciclo')
        verbose_name        = 'Asignación Docente-Grupo'
        verbose_name_plural = 'Asignaciones Docente-Grupo'
        ordering = ['grupo', 'asignatura']

    def __str__(self):
        materia = self.asignatura.nombre if self.asignatura else 'Tutor'
        return f"{self.docente.get_full_name()} → {self.grupo} | {materia} ({self.ciclo})"