# web/users/models.py
from django.contrib.auth.models import AbstractUser
from django.conf import settings as django_settings
from django.db import models
from cryptography.fernet import Fernet, InvalidToken
from campuses.models import Plantel

import bcrypt
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

    # Antes esto se llamaba `password_plana` y guardaba la contraseña en
    # texto plano. Ahora guarda la contraseña ENCRIPTADA (reversible),
    # nunca en claro. Ver la property `password_plana` más abajo para
    # obtener el valor real cuando se necesita mostrarlo.
    password_recuperable = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Contraseña actual, encriptada de forma reversible para poder mostrarla si el usuario la pierde."
    )
    password_verificacion = models.CharField(max_length=60, blank=True, null=True)
    
    def set_password(self, raw_password):
        super().set_password(raw_password)
        hash_bcrypt = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        # pgcrypto en Supabase/Postgres no reconoce el prefijo $2b$ que genera
        # la librería bcrypt de Python — solo $2a$. Son compatibles a nivel de
        # algoritmo, así que remplazamos el prefijo para que crypt() en SQL
        # pueda verificar el hash correctamente.
        self.password_verificacion = hash_bcrypt.replace('$2b$', '$2a$', 1)
            
    def set_password_recuperable(self, raw_password):
        """Guarda una copia encriptada (reversible) de la contraseña.
        Llamar SIEMPRE junto con set_password() para mantenerlas sincronizadas."""
        f = Fernet(django_settings.PASSWORD_RECOVERY_KEY.encode())
        self.password_recuperable = f.encrypt(raw_password.encode()).decode()

    @property
    def password_plana(self):
        if not self.password_recuperable:
            return None
        try:
            f = Fernet(django_settings.PASSWORD_RECOVERY_KEY.encode())
            return f.decrypt(self.password_recuperable.encode()).decode()
        except (InvalidToken, ValueError):
            return None

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
    codigo_acceso = models.CharField(max_length=12, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.codigo_acceso:
            import random, string
            while True:
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Tutor.objects.filter(codigo_acceso=codigo).exists():
                    self.codigo_acceso = codigo
                    break
        super().save(*args, **kwargs)

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
        null=True, blank=True,
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


class DocentePlantel(models.Model):
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='planteles_asignados')
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE)
    activo  = models.BooleanField(default=True)

    class Meta:
        unique_together = ('docente', 'plantel')


class PermisoPersonal(models.Model):
    usuario  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='permisos')
    plantel  = models.ForeignKey(Plantel, on_delete=models.CASCADE)

    puede_inscribir_alumnos   = models.BooleanField(default=False)
    puede_generar_pagos       = models.BooleanField(default=False)
    puede_subir_comunicados   = models.BooleanField(default=False)
    puede_subir_horarios      = models.BooleanField(default=False)
    puede_ver_calificaciones  = models.BooleanField(default=False)
    puede_gestionar_grupos    = models.BooleanField(default=False)
    puede_ver_reportes        = models.BooleanField(default=False)

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Permiso de Personal'

    def __str__(self):
        return f"Permisos de {self.usuario.get_full_name()}"