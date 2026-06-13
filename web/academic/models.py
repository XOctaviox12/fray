from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from campuses.models import Plantel
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


# ==========================================
# 1. CATÁLOGOS Y ESTRUCTURA
# ==========================================

class Periodo(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    plantel = models.ForeignKey(
        'campuses.Plantel',
        on_delete=models.CASCADE,
        related_name='periodos',
        null=True, blank=True
    )
    nombre = models.CharField(max_length=50)

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
        from django.db.models import Count, Case, When, IntegerField
        now = timezone.now()
        resultado = Asistencia.objects.filter(
            grupo=self, fecha__month=now.month
        ).aggregate(
            total=Count('id'),
            presentes=Count(Case(When(estado='P', then=1), output_field=IntegerField()))
        )
        total = resultado['total']
        if total == 0:
            return 0
        return int((resultado['presentes'] / total) * 100)


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
    TIPOS = [
        ('MANUAL',     'Captura manual'),
        ('TAREA',      'Tarea'),
        ('ACTIVIDAD',  'Actividad'),
    ]
    alumno     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notas')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='calificaciones')
    grupo      = models.ForeignKey('Grupo', on_delete=models.CASCADE, related_name='calificaciones', null=True, blank=True)
    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calificaciones_dadas', null=True, blank=True)
    nota       = models.DecimalField(max_digits=4, decimal_places=2)
    tipo       = models.CharField(max_length=15, choices=TIPOS, default='MANUAL')
    fecha      = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.alumno} — {self.asignatura}: {self.nota}"


class Asistencia(models.Model):
    ESTADOS = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('R', 'Retardo'),
    ]

    alumno   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='asistencias')
    grupo    = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='asistencias')
    asignatura = models.ForeignKey(
        'Asignatura',
        on_delete=models.CASCADE,
        related_name='asistencias',
        null=True, blank=True,
    )
    fecha    = models.DateField(default=timezone.now)   # <-- ya no auto_now_add para poder editar
    estado   = models.CharField(max_length=1, choices=ESTADOS, default='P')

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ['-fecha']
        unique_together = [['alumno', 'grupo', 'asignatura', 'fecha']]

    @property
    def presente(self):
        """Compatibilidad hacia atrás con código que use .presente"""
        return self.estado == 'P'

    def __str__(self):
        return f"{self.alumno} — {self.grupo} — {self.fecha} ({self.get_estado_display()})"

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

        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                errors['hora_fin'] = 'La hora de fin debe ser posterior a la de inicio.'

        if not errors:

            # 1. Colisión de MAESTRO (sin filtro de plantel — un maestro no puede
            #    estar en dos lugares a la vez aunque sean planteles distintos)
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

            # 2. Colisión de GRUPO (dentro del mismo plantel)
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

            # 3. Colisión de AULA — solo dentro del mismo plantel (Fix crítico)
            if self.aula and self.aula != "Por definir" and self.grupo_id:
                conflicto_aula = HorarioClase.objects.filter(
                    dia=self.dia,
                    aula=self.aula,
                    grupo__plantel=self.grupo.plantel,   # ← Fix: solo mismo plantel
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


class Tarea(models.Model):
    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tareas_creadas')
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='tareas')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='tareas')
    titulo     = models.CharField(max_length=200)
    descripcion= models.TextField(blank=True)
    archivo = CloudinaryField('archivo', resource_type='raw',type='upload', blank=True, null=True)
    fecha_entrega = models.DateTimeField()
    creada_en  = models.DateTimeField(auto_now_add=True)
    activa     = models.BooleanField(default=True)
    publicada  = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return f"{self.titulo} — {self.grupo} | {self.asignatura}"

    @property
    def vencida(self):
        from django.utils import timezone
        return timezone.now() > self.fecha_entrega


class EntregaTarea(models.Model):
    ESTADOS = [
        ('PENDIENTE',   'Pendiente'),
        ('ENTREGADA',   'Entregada'),
        ('CALIFICADA',  'Calificada'),
        ('TARDE',       'Entrega tardía'),
    ]
    tarea     = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas')
    alumno    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entregas')
    archivo = CloudinaryField('archivo', resource_type='raw',type='upload')
    comentario= models.TextField(blank=True)
    estado    = models.CharField(max_length=15, choices=ESTADOS, default='ENTREGADA')
    calificacion = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    feedback  = models.TextField(blank=True)
    entregada_en = models.DateTimeField(auto_now_add=True)
    calificada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['tarea', 'alumno']]
        ordering = ['-entregada_en']

    def __str__(self):
        return f"{self.alumno} → {self.tarea.titulo}"


class ComentarioTarea(models.Model):
    tarea   = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='comentarios')
    autor   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comentarios_tarea')
    texto   = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado_en']

class Actividad(models.Model):
    TIPOS = [
        ('ABIERTA',    'Pregunta abierta'),
        ('MULTIPLE',   'Opción múltiple'),
        ('ARCHIVO',    'Subir archivo'),
        ('INTERACTIVA','Ejercicio interactivo'),
    ]
    docente       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    grupo         = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    asignatura    = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    titulo        = models.CharField(max_length=200)
    instrucciones = models.TextField(blank=True)
    tipo          = models.CharField(max_length=15, choices=TIPOS)
    archivo       = CloudinaryField('archivo', resource_type='raw', type='upload', blank=True, null=True)
    url_interactiva = models.URLField(blank=True, null=True)  # GeoGebra, Kahoot, Quizlet, etc.
    fecha_entrega = models.DateTimeField()
    calificacion_automatica = models.BooleanField(default=False)
    valor_total   = models.DecimalField(max_digits=4, decimal_places=2, default=10)
    creada_en     = models.DateTimeField(auto_now_add=True)
    publicada    = models.BooleanField(default=False)
    publicada_en = models.DateTimeField(null=True, blank=True)

    @property
    def vencida(self):
        return timezone.now() > self.fecha_entrega

class PreguntaActividad(models.Model):
    actividad  = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='preguntas')
    texto      = models.TextField()
    orden      = models.IntegerField(default=0)
    puntos     = models.DecimalField(max_digits=4, decimal_places=2, default=1)

class OpcionRespuesta(models.Model):
    pregunta   = models.ForeignKey(PreguntaActividad, on_delete=models.CASCADE, related_name='opciones')
    texto      = models.CharField(max_length=300)
    es_correcta = models.BooleanField(default=False)

class EntregaActividad(models.Model):
    actividad    = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='entregas')
    alumno       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    archivo      = CloudinaryField('archivo', resource_type='raw', type='upload', blank=True, null=True)
    calificacion = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    feedback     = models.TextField(blank=True)
    entregada_en = models.DateTimeField(auto_now_add=True)

class RespuestaAlumno(models.Model):
    entrega   = models.ForeignKey(EntregaActividad, on_delete=models.CASCADE, related_name='respuestas')
    pregunta  = models.ForeignKey(PreguntaActividad, on_delete=models.CASCADE)
    texto     = models.TextField(blank=True)       # para preguntas abiertas
    opcion    = models.ForeignKey(OpcionRespuesta, on_delete=models.SET_NULL, null=True, blank=True)  # para opción múltiple

class CarpetaMaterial(models.Model):
    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carpetas_material')
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='carpetas_material')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='carpetas_material')
    nombre     = models.CharField(max_length=100)
    descripcion= models.TextField(blank=True)
    orden      = models.IntegerField(default=0)
    creada_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Carpeta de Material'

    def __str__(self):
        return f"{self.nombre} — {self.asignatura} | {self.grupo}"


class MaterialApoyo(models.Model):
    TIPOS = [
        ('PDF',    'PDF / Documento'),
        ('VIDEO',  'Video'),
        ('IMAGEN', 'Imagen'),
        ('LINK',   'Enlace externo'),
        ('OTRO',   'Otro'),
    ]

    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='materiales')
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='materiales')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='materiales')
    carpeta    = models.ForeignKey(CarpetaMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiales')
    titulo     = models.CharField(max_length=200)
    descripcion= models.TextField(blank=True)
    tipo       = models.CharField(max_length=10, choices=TIPOS)
    archivo    = CloudinaryField('archivo', resource_type='auto', type='upload', blank=True, null=True)
    url_externa= models.URLField(blank=True, null=True)
    orden      = models.IntegerField(default=0)
    creado_en  = models.DateTimeField(auto_now_add=True)
    activo     = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', '-creado_en']
        verbose_name = 'Material de Apoyo'

    def __str__(self):
        return f"{self.titulo} — {self.asignatura}"

    @property
    def icono(self):
        return {'PDF':'📄','VIDEO':'🎬','IMAGEN':'🖼️','LINK':'🔗','OTRO':'📎'}.get(self.tipo,'📎')

    @property
    def es_youtube(self):
        return self.url_externa and ('youtube.com' in self.url_externa or 'youtu.be' in self.url_externa)

    @property
    def youtube_embed(self):
        if not self.es_youtube:
            return None
        url = self.url_externa
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in url:
            vid = url.split('v=')[1].split('&')[0]
        else:
            return None
        return f"https://www.youtube.com/embed/{vid}"


class ComentarioMaterial(models.Model):
    material  = models.ForeignKey(MaterialApoyo, on_delete=models.CASCADE, related_name='comentarios')
    autor     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto     = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado_en']

# ─────────────────────────────────────────────────────────────────────────────
# PLANIFICACIÓN CURRICULAR
# ─────────────────────────────────────────────────────────────────────────────

class PlanClase(models.Model):
    """Plan de clase semanal/mensual creado por un docente para una asignatura y grupo."""

    PERIODOS = [
        ('SEMANA',    'Semanal'),
        ('QUINCENA',  'Quincenal'),
        ('MES',       'Mensual'),
        ('BIMESTRE',  'Bimestral'),
        ('SEMESTRE',  'Semestral'),
        ('ANUAL',     'Anual'),
    ]

    docente    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='planes_clase',
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='planes_clase',
    )
    grupo      = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='planes_clase',
    )
    titulo         = models.CharField(max_length=200)
    descripcion    = models.TextField(blank=True)
    periodo_tipo   = models.CharField(max_length=20, choices=PERIODOS, default='MES')
    fecha_inicio   = models.DateField()
    fecha_fin      = models.DateField()
    objetivo_general = models.TextField(blank=True, verbose_name='Objetivo general')
    competencias   = models.TextField(blank=True, verbose_name='Competencias a desarrollar')
    publicado      = models.BooleanField(default=False)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Plan de Clase'
        verbose_name_plural = 'Planes de Clase'
        ordering            = ['-fecha_inicio']

    def __str__(self):
        return f"{self.titulo} — {self.asignatura} ({self.grupo})"

    @property
    def progreso(self):
        """Porcentaje de temas marcados como completados."""
        total = self.temas.count()
        if total == 0:
            return 0
        completados = self.temas.filter(completado=True).count()
        return int((completados / total) * 100)


class TemaClase(models.Model):
    """Tema/sesión individual dentro de un PlanClase."""

    plan        = models.ForeignKey(PlanClase, on_delete=models.CASCADE, related_name='temas')
    numero      = models.PositiveIntegerField(verbose_name='# Sesión')
    titulo      = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha       = models.DateField(null=True, blank=True)
    duracion_min = models.PositiveIntegerField(default=50, verbose_name='Duración (min)')
    recursos    = models.TextField(blank=True, verbose_name='Recursos / materiales')
    evaluacion  = models.TextField(blank=True, verbose_name='Instrumento de evaluación')
    completado  = models.BooleanField(default=False)
    notas_docente = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Tema / Sesión'
        verbose_name_plural = 'Temas / Sesiones'
        ordering            = ['numero']
        unique_together     = [['plan', 'numero']]

    def __str__(self):
        return f"Sesión {self.numero}: {self.titulo}"