from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from users.models import Plantel
from django.core.exceptions import ValidationError


# ==========================================
# 1. CATÁLOGOS Y ESTRUCTURA
# ==========================================

class Periodo(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    NIVELES = [
        ('SECUNDARIA',   'Secundaria'),
        ('PREPARATORIA', 'Preparatoria'),
        ('UNIVERSIDAD',  'Universidad'),
    ]

    plantel    = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name='carreras')
    nombre     = models.CharField(max_length=150)
    nivel      = models.CharField(max_length=20, choices=NIVELES)
    clave_rvoe = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nivel})"


# ==========================================
# 2. GRUPOS
# ==========================================

class Grupo(models.Model):
    plantel  = models.ForeignKey(Plantel,  on_delete=models.CASCADE, related_name='grupos')
    carrera  = models.ForeignKey(Carrera,  on_delete=models.CASCADE, related_name='grupos',  null=True, blank=True)
    periodo  = models.ForeignKey(Periodo,  on_delete=models.SET_NULL, null=True, blank=True)

    nombre           = models.CharField(max_length=50)
    grado            = models.IntegerField(verbose_name="Grado o Semestre")
    aula             = models.CharField(max_length=50, null=True, blank=True)
    capacidad_maxima = models.IntegerField(default=30)

    docentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='grupos_asignados',
        limit_choices_to={'rol': 'DOCENTE'},
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['grado', 'nombre']

    # ── Un solo __str__ limpio ──────────────────────────────────────
    def __str__(self):
        nombre_carrera = self.carrera.nombre if self.carrera else "General"
        return f"{nombre_carrera} — {self.grado}º {self.nombre}"

    # ── KPIs ────────────────────────────────────────────────────────
    @property
    def ocupacion_porcentaje(self):
        if self.capacidad_maxima > 0:
            return round((self.alumnos.count() / self.capacidad_maxima) * 100, 1)
        return 0

    @property
    def promedio_general(self):
        val = Calificacion.objects.filter(
            asignatura__grupos=self
        ).distinct().aggregate(promedio=Avg('nota'))['promedio']
        return round(float(val), 2) if val else 0.0

    @property
    def asistencia_mensual(self):
        now   = timezone.now()
        total = Asistencia.objects.filter(grupo=self, fecha__month=now.month).count()
        if total == 0:
            return 0
        presentes = Asistencia.objects.filter(
            grupo=self, fecha__month=now.month, presente=True
        ).count()
        return int((presentes / total) * 100)


# ==========================================
# 3. ACADÉMICO
# ==========================================

class Asignatura(models.Model):
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        related_name='asignaturas_de_carrera',
    )
    grupos = models.ManyToManyField(
        Grupo,
        related_name='asignaturas',
        verbose_name="Grupos",
        blank=True,
    )
    docentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='materias_impartidas',
    )

    nombre    = models.CharField(max_length=100)
    clave     = models.CharField(max_length=20, blank=True, null=True)
    creditos  = models.IntegerField(default=0,  blank=True, null=True)
    seriacion = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='materias_subsecuentes',
    )

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Calificacion(models.Model):
    alumno     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notas')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='calificaciones')
    nota       = models.DecimalField(max_digits=4, decimal_places=2)
    fecha      = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.alumno} — {self.asignatura}: {self.nota}"


class Asistencia(models.Model):
    alumno   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='asistencias')
    grupo    = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='asistencias')
    fecha    = models.DateField(auto_now_add=True)
    presente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ['-fecha']
        # Evita duplicar el registro del mismo alumno en el mismo día
        unique_together = [['alumno', 'grupo', 'fecha']]

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.alumno} — {self.grupo} — {self.fecha} ({estado})"


# ==========================================
# 4. HORARIOS
# ==========================================

class HorarioClase(models.Model):
    DIAS_SEMANA = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
    ]

    # ✅ CORRECCIÓN: era 'MAESTRO', ahora 'DOCENTE' para coincidir con User.rol
    asignatura  = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='horarios')
    maestro     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='clases_asignadas',
    )
    grupo       = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='horarios')
    dia         = models.CharField(max_length=2, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    aula        = models.CharField(max_length=50, default="Por definir")
    activo      = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de Clase"
        verbose_name_plural = "Horarios de Clases"
        ordering = ['dia', 'hora_inicio']

    def __str__(self):
        return f"{self.asignatura.nombre} | {self.get_dia_display()} {self.hora_inicio:%H:%M}"

    # ── Validaciones de integridad ───────────────────────────────────
    def clean(self):
        errors = {}

        # 1. Hora fin debe ser posterior a hora inicio
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                errors['hora_fin'] = 'La hora de fin debe ser posterior a la de inicio.'

        # Solo seguimos si las horas son válidas
        if not errors:

            # 2. Colisión de MAESTRO
            if self.maestro_id:
                conflicto_maestro = HorarioClase.objects.filter(
                    dia=self.dia,
                    maestro=self.maestro,
                    activo=True,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio,
                ).exclude(pk=self.pk)

                if conflicto_maestro.exists():
                    clase = conflicto_maestro.first()
                    errors['maestro'] = (
                        f'El docente ya tiene "{clase.asignatura}" asignada '
                        f'los {self.get_dia_display()} en ese horario.'
                    )

            # 3. Colisión de GRUPO
            if self.grupo_id:
                conflicto_grupo = HorarioClase.objects.filter(
                    dia=self.dia,
                    grupo=self.grupo,
                    activo=True,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio,
                ).exclude(pk=self.pk)

                if conflicto_grupo.exists():
                    clase = conflicto_grupo.first()
                    errors['grupo'] = (
                        f'El grupo ya tiene "{clase.asignatura}" '
                        f'los {self.get_dia_display()} en ese horario.'
                    )

            # 4. Colisión de AULA (solo si está definida)
            if self.aula and self.aula != "Por definir":
                conflicto_aula = HorarioClase.objects.filter(
                    dia=self.dia,
                    aula=self.aula,
                    activo=True,
                    hora_inicio__lt=self.hora_fin,
                    hora_fin__gt=self.hora_inicio,
                ).exclude(pk=self.pk)

                if conflicto_aula.exists():
                    errors['aula'] = f'El aula "{self.aula}" ya está ocupada en ese horario.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)