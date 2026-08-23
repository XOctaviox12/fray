from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from campuses.models import Plantel
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from decimal import Decimal
from django.db import migrations
from django.db.models import UniqueConstraint, Q


# ==========================================
# 1. CATÁLOGOS Y ESTRUCTURA
# ==========================================

def poblar_periodo_historico(apps, schema_editor):
    Tarea = apps.get_model('academic', 'Tarea')
    Asistencia = apps.get_model('academic', 'Asistencia')
    Actividad = apps.get_model('academic', 'Actividad')
    EvaluacionParcial = apps.get_model('academic', 'EvaluacionParcial')

    for modelo in [Tarea, Asistencia, Actividad, EvaluacionParcial]:
        for obj in modelo.objects.filter(periodo__isnull=True).select_related('grupo'):
            if obj.grupo_id and obj.grupo.periodo_id:
                obj.periodo_id = obj.grupo.periodo_id
                obj.save(update_fields=['periodo'])


def revertir(apps, schema_editor):
    # No hay nada que revertir de forma segura: no queremos volver a poner
    # periodo=NULL sobre datos ya poblados. No-op intencional.
    pass


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ ajusta esto al nombre real de tu migración anterior,
        # la que agregó los campos `periodo` a los 4 modelos
        ('academic', '00XX_agregar_periodo_a_modelos'),
    ]

    operations = [
        migrations.RunPython(poblar_periodo_historico, revertir),
    ]

class Periodo(models.Model):
    TIPOS = [
        ('NON', 'Non (Agosto–Enero)'),
        ('PAR', 'Par (Febrero–Junio)'),
    ]

    MESES_COMPLETO = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
    }
    MESES_ABREVIADO = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic',
    }

    tipo = models.CharField(
        max_length=50,
        default='regular'  
    )
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

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ['-fecha_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['plantel'],
                condition=models.Q(activo=True),
                name='uq_periodo_un_activo_por_plantel',
            ),
        ]

    def __str__(self):
        return self.nombre

    def get_display_name(self, corto=False):
        """Devuelve el período en español, ej: '2027 Febrero–Junio (PAR)'.
        Si corto=True: '2027 Feb–Jun (PAR)'.
        Si faltan fechas, cae en self.nombre como respaldo."""
        if not self.fecha_inicio or not self.fecha_fin:
            return self.nombre

        meses = self.MESES_ABREVIADO if corto else self.MESES_COMPLETO
        mes_inicio = meses.get(self.fecha_inicio.month, '')
        mes_fin = meses.get(self.fecha_fin.month, '')
        anio = self.fecha_fin.year

        return f"{anio} {mes_inicio}–{mes_fin} ({self.tipo})"

    def cerrar(self):
        """Cierra este periodo. Bloquea nuevas tareas/asistencias/
        actividades/calificaciones para todos los grupos de este
        plantel que estén ligados a él; los registros ya creados siguen
        consultables sin restricción."""
        self.activo = False
        self.save(update_fields=['activo'])

    def promover_ciclo(self):
        """Cierra este periodo, crea el siguiente Periodo del mismo
        plantel, y para cada Grupo de este periodo:
        - Si el siguiente grado no es 5° ni pasa de 6°: crea el Grupo
          del siguiente grado (misma carrera/aula/docentes) y pasa
          automáticamente a todos sus alumnos.
        - Si el siguiente grado es 5° (viene de 4°): NO crea nada ni
          mueve alumnos — requiere que el director asigne especialidad
          a mano. Se devuelven esos alumnos para que la UI se los
          muestre.
        - Si el grupo es de 6° (egreso): no se crea grupo nuevo.
        Devuelve (nuevo_periodo, alumnos_pendientes_especialidad).
        """
        from django.db import transaction

        if not self.activo:
            raise ValidationError('Este periodo ya estaba cerrado.')

        with transaction.atomic():
            self.cerrar()

            anio_ref = self.fecha_fin.year if self.fecha_fin else self.fecha_inicio.year

            if self.tipo == 'NON':
                nuevo_tipo = 'PAR'
                nueva_fecha_inicio = self.fecha_fin.replace(month=2, day=1) if self.fecha_fin else None
                nueva_fecha_fin = self.fecha_fin.replace(month=6, day=30) if self.fecha_fin else None
                nuevo_nombre = f"{anio_ref} Febrero–Junio"
            else:
                nuevo_tipo = 'NON'
                nueva_fecha_inicio = self.fecha_fin.replace(month=8, day=1) if self.fecha_fin else None
                nueva_fecha_fin = self.fecha_fin.replace(year=anio_ref + 1, month=1, day=31) if self.fecha_fin else None
                nuevo_nombre = f"{anio_ref} Agosto–Enero"

            nuevo_periodo = Periodo.objects.create(
                nombre=nuevo_nombre,
                tipo=nuevo_tipo,
                fecha_inicio=nueva_fecha_inicio,
                fecha_fin=nueva_fecha_fin,
                activo=True,
                plantel=self.plantel,
            )

            alumnos_pendientes = []

            for grupo in self.plantel.grupos.filter(periodo=self):
                grado_siguiente = grupo.grado + 1

                if grado_siguiente == 5:
                    alumnos_pendientes.extend(grupo.alumnos.all())
                    continue

                if grado_siguiente > 6:
                    continue

                nuevo_grupo = Grupo.objects.create(
                    plantel=grupo.plantel,
                    carrera=grupo.carrera,
                    periodo=nuevo_periodo,
                    nombre=grupo.nombre,
                    grado=grado_siguiente,
                    aula=grupo.aula,
                    capacidad_maxima=grupo.capacidad_maxima,
                )
                nuevo_grupo.docentes.set(grupo.docentes.all())
                grupo.alumnos.update(alumno_grupo=nuevo_grupo)

        return nuevo_periodo, alumnos_pendientes
        

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
    ESPECIALIDADES = [
        ('QUIMICO_BIOLOGICO', 'Químico-Biológico'),
        ('FISICO_QUIMICO',    'Físico-Químico'),
        ('ECONOMICO_ADMIN',   'Económico-Administrativo'),
        ('HISTORICO_SOCIAL',  'Histórico-Social'),
    ]

    plantel  = models.ForeignKey(Plantel,  on_delete=models.CASCADE, related_name='grupos')
    carrera  = models.ForeignKey(Carrera,  on_delete=models.CASCADE, related_name='grupos',  null=True, blank=True)
    periodo  = models.ForeignKey(Periodo,  on_delete=models.SET_NULL, null=True, blank=True)

    nombre           = models.CharField(max_length=50)
    grado            = models.IntegerField(verbose_name="Grado o Semestre")
    especialidad     = models.CharField(
        max_length=30, choices=ESPECIALIDADES, null=True, blank=True,
        help_text='Solo aplica de 5° a 6° semestre en Preparatoria.'
    )
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
        constraints = [
            UniqueConstraint(
                fields=['plantel', 'periodo', 'carrera', 'grado'],
                condition=Q(especialidad__isnull=True),
                name='unique_grupo_general_sin_especialidad',
            ),
            UniqueConstraint(
                fields=['plantel', 'periodo', 'carrera', 'grado', 'especialidad'],
                condition=Q(especialidad__isnull=False),
                name='unique_grupo_por_especialidad',
            ),
        ]
    def save(self, *args, **kwargs):
        # Generar nombre automático basado en grado y especialidad
        especialidad_label = dict(self.ESPECIALIDADES).get(self.especialidad)
        if especialidad_label:
            self.nombre = f"{self.grado}° Semestre - {especialidad_label}"
        else:
            self.nombre = f"{self.grado}° Semestre"

        super().save(*args, **kwargs)
    def __str__(self):
        nombre_carrera = self.carrera.nombre if self.carrera else "General"
        return f"{nombre_carrera} — {self.grado}º {self.nombre}"

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
    asignatura = models.ForeignKey('Asignatura', on_delete=models.CASCADE, related_name='asistencias', null=True, blank=True)
    periodo  = models.ForeignKey(
        Periodo, on_delete=models.PROTECT,
        related_name='asistencias', editable=False, null=True, blank=True,
    )
    fecha    = models.DateField(default=timezone.now)
    estado   = models.CharField(max_length=1, choices=ESTADOS, default='P')
    parcial  = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ['-fecha']
        unique_together = [['alumno', 'grupo', 'asignatura', 'fecha']]

    @property
    def presente(self):
        return self.estado == 'P'

    def __str__(self):
        return f"{self.alumno} — {self.grupo} — {self.fecha} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if self.grupo_id and not self.pk:
            periodo_grupo = self.grupo.periodo
            if not periodo_grupo or not periodo_grupo.activo:
                raise ValidationError('El ciclo de este grupo ya fue cerrado por el director. No se puede pasar lista.')
            self.periodo = periodo_grupo
        super().save(*args, **kwargs)

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
    periodo    = models.ForeignKey(
        Periodo, on_delete=models.PROTECT,
        related_name='tareas', editable=False, null=True, blank=True,
    )
    titulo     = models.CharField(max_length=200)
    descripcion= models.TextField(blank=True)
    archivo = CloudinaryField('archivo', resource_type='raw', type='upload', blank=True, null=True)
    fecha_entrega = models.DateTimeField()
    creada_en  = models.DateTimeField(auto_now_add=True)
    activa     = models.BooleanField(default=True)
    publicada  = models.BooleanField(default=False)
    parcial = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return f"{self.titulo} — {self.grupo} | {self.asignatura}"

    @property
    def vencida(self):
        from django.utils import timezone
        return timezone.now() > self.fecha_entrega

    def save(self, *args, **kwargs):
        if self.grupo_id and not self.pk:
            periodo_grupo = self.grupo.periodo
            if not periodo_grupo or not periodo_grupo.activo:
                raise ValidationError('El ciclo de este grupo ya fue cerrado por el director. No se pueden crear nuevas tareas.')
            self.periodo = periodo_grupo
        super().save(*args, **kwargs)

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
    periodo       = models.ForeignKey(
        Periodo, on_delete=models.PROTECT,
        related_name='actividades', editable=False, null=True, blank=True,
    )
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
    parcial = models.PositiveSmallIntegerField(default=1)

    @property
    def vencida(self):
        return timezone.now() > self.fecha_entrega

    def save(self, *args, **kwargs):
        if self.grupo_id and not self.pk:
            periodo_grupo = self.grupo.periodo
            if not periodo_grupo or not periodo_grupo.activo:
                raise ValidationError('El ciclo de este grupo ya fue cerrado por el director. No se pueden crear nuevas actividades.')
            self.periodo = periodo_grupo
        super().save(*args, **kwargs)

class PreguntaActividad(models.Model):
    TIPOS = [
        ('opcion_multiple', 'Opción múltiple'),
        ('verdadero_falso', 'Verdadero / Falso'),
        ('respuesta_corta', 'Respuesta corta'),
    ]
    actividad  = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='preguntas')
    tipo       = models.CharField(max_length=20, choices=TIPOS, default='opcion_multiple')
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
 
    ESTADOS = [
        ('borrador',   'Borrador'),
        ('activa',     'Activa'),
        ('finalizada', 'Finalizada'),
    ]
 
    TIPOS_BLOQUE = ('texto', 'pdf', 'video', 'actividad', 'imagen', 'link')
 
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
 
    # ── Campos agregados para Clase en Vivo ─────────────────────────
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
 
    # Copia de docente/grupo/asignatura del plan padre. Se llenan solos
    # en save(). Existen porque Supabase Realtime solo puede filtrar por
    # columnas de la propia tabla (no puede filtrar a través de un JOIN
    # con PlanClase), así que la app móvil necesita estos campos aquí
    # mismo para saber a quién mostrarle la sesión en vivo.
    docente    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='temas_clase',
        editable=False,
        null=True, blank=True,
    )
    grupo      = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='temas_clase',
        editable=False,
        null=True, blank=True,
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='temas_clase',
        editable=False,
        null=True, blank=True,
    )
 
    # Contenido en vivo: lista de bloques ordenados.
    # Ej: [{"id": "b1", "tipo": "texto", "titulo": "", "contenido": "...", "orden": 1}, ...]
    bloques = models.JSONField(default=list, blank=True)
 
    iniciada_en   = models.DateTimeField(null=True, blank=True)
    finalizada_en = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        verbose_name        = 'Tema / Sesión'
        verbose_name_plural = 'Temas / Sesiones'
        ordering            = ['numero']
        unique_together     = [['plan', 'numero']]
        constraints = [
            # Un docente solo puede tener UNA sesión activa (transmitiendo)
            # a la vez, sin importar de qué plan/grupo/materia sea.
            models.UniqueConstraint(
                fields=['docente'],
                condition=models.Q(estado='activa'),
                name='uq_temaclase_docente_una_activa',
            ),
        ]
 
    def __str__(self):
        return f"Sesión {self.numero}: {self.titulo}"
 
    def save(self, *args, **kwargs):
        # Denormaliza docente/grupo/asignatura desde el plan padre
        if self.plan_id:
            self.docente_id    = self.plan.docente_id
            self.grupo_id      = self.plan.grupo_id
            self.asignatura_id = self.plan.asignatura_id
        super().save(*args, **kwargs)
 
    # ── Helpers de transmisión en vivo ──────────────────────────────
 
    def iniciar_transmision(self):
        """Activa esta sesión y finaliza cualquier otra activa del mismo docente."""
        from django.utils import timezone
 
        TemaClase.objects.filter(
            docente_id=self.docente_id, estado='activa'
        ).exclude(pk=self.pk).update(estado='finalizada', finalizada_en=timezone.now())
 
        self.estado = 'activa'
        self.iniciada_en = timezone.now()
        self.save(update_fields=['estado', 'iniciada_en'])
 
    def finalizar_transmision(self):
        from django.utils import timezone
 
        self.estado = 'finalizada'
        self.finalizada_en = timezone.now()
        self.completado = True
        self.save(update_fields=['estado', 'finalizada_en', 'completado'])
 
    def agregar_bloque(self, tipo, contenido, titulo=''):
        if tipo not in self.TIPOS_BLOQUE:
            raise ValueError(f'Tipo de bloque inválido: {tipo}')
 
        import uuid
        nuevo = {
            'id': uuid.uuid4().hex[:8],
            'tipo': tipo,
            'titulo': titulo,
            'contenido': contenido,
            'orden': len(self.bloques) + 1,
        }
        self.bloques = [*self.bloques, nuevo]
        self.save(update_fields=['bloques'])
        return nuevo
 
    def eliminar_bloque(self, bloque_id):
        self.bloques = [b for b in self.bloques if b.get('id') != bloque_id]
        self.save(update_fields=['bloques']) 
# ══════════════════════════════════════════════════════════════════════════════
# 1. MODELO — agregar al final de academic/models.py
# ══════════════════════════════════════════════════════════════════════════════
 
class Comunicado(models.Model):
    DESTINATARIOS = [
        ('TODOS',    'Todos los grupos'),
        ('GRUPO',    'Grupo específico'),
        ('DOCENTES', 'Solo docentes'),
    ]

    # A quién le llega dentro del destinatario elegido: solo alumnos,
    # solo padres/tutores, o ambos. Corresponde a la columna `publico`
    # agregada directamente en Supabase con:
    #   ALTER TABLE academic_comunicado ADD COLUMN publico varchar DEFAULT 'AMBOS';
    PUBLICO_OPCIONES = [
        ('ALUMNOS', 'Solo alumnos'),
        ('PADRES',  'Solo padres'),
        ('AMBOS',   'Alumnos y padres'),
    ]

    plantel     = models.ForeignKey(
        'campuses.Plantel',
        on_delete=models.CASCADE,
        related_name='comunicados',
    )
    autor       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comunicados_enviados',
    )
    titulo      = models.CharField(max_length=200)
    cuerpo      = models.TextField()
    destinatario = models.CharField(max_length=10, choices=DESTINATARIOS, default='TODOS')
    publico     = models.CharField(
        max_length=10,
        choices=PUBLICO_OPCIONES,
        default='AMBOS',
        help_text='A quién le llega: solo alumnos, solo padres, o ambos.',
    )
    grupo       = models.ForeignKey(
        'Grupo',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='comunicados',
        help_text='Solo si destinatario es GRUPO',
    )
    # Django genera automáticamente la columna `asignatura_id`, igual a la
    # que se agregó por SQL con:
    #   ALTER TABLE academic_comunicado ADD COLUMN asignatura_id int8
    #     REFERENCES academic_asignatura(id);
    asignatura  = models.ForeignKey(
        'Asignatura',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='comunicados',
        help_text='Materia relacionada (opcional). Vacío = comunicado general.',
    )
    adjunto     = CloudinaryField(
        'adjunto',
        resource_type='auto',
        blank=True, null=True,
        help_text='PDF, imagen u otro archivo adjunto (opcional)',
    )
    creado_en   = models.DateTimeField(auto_now_add=True)
    activo      = models.BooleanField(default=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Comunicado'
        verbose_name_plural = 'Comunicados'

    def __str__(self):
        return f"{self.titulo} — {self.plantel}"
    
class HorarioPDF(models.Model):
    grupo    = models.OneToOneField(Grupo, on_delete=models.CASCADE, related_name='horario_pdf')
    plantel  = models.ForeignKey(Plantel, on_delete=models.CASCADE, related_name='horarios_pdf')
    archivo  = CloudinaryField('horario', resource_type='raw', type='upload')
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    subido_en  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Horario PDF'

    def __str__(self):
        return f"Horario — {self.grupo}"
    
class ConfigEvaluacion(models.Model):
    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='configs_evaluacion')
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='configs_evaluacion')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='configs_evaluacion')

    pct_tareas      = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    pct_actividades = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    pct_asistencia  = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    pct_examen      = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    pct_proyecto    = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    rubros_extra = models.JSONField(default=list, blank=True)   # <- si esta línea no existe, agrégala

    class Meta:
        unique_together = [['docente', 'grupo', 'asignatura']]
        verbose_name = 'Configuración de Evaluación'

    def total(self):
        extra = sum((Decimal(str(r.get('pct', 0) or 0)) for r in self.rubros_extra), Decimal('0'))
        return self.pct_tareas + self.pct_actividades + self.pct_asistencia + self.pct_examen + self.pct_proyecto + extra

    def __str__(self):
        return f"Config {self.asignatura} — {self.grupo}"
    
class EvaluacionParcial(models.Model):
    RUBROS = [
        ('EXAMEN',   'Examen'),
        ('PROYECTO', 'Proyecto'),
    ]
    alumno     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_parciales')
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='evaluaciones_parciales')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='evaluaciones_parciales')
    docente    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_dadas')
    periodo    = models.ForeignKey(
        Periodo, on_delete=models.PROTECT,
        related_name='evaluaciones_parciales', editable=False, null=True, blank=True,
    )
    rubro      = models.CharField(max_length=30, choices=RUBROS)
    nota       = models.DecimalField(max_digits=4, decimal_places=2)
    observacion= models.TextField(blank=True)
    fecha      = models.DateField(auto_now_add=True)
    parcial = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = [['alumno', 'grupo', 'asignatura', 'rubro', 'parcial']]
        verbose_name = 'Evaluación Parcial'

    def __str__(self):
        return f"{self.alumno} — {self.rubro}: {self.nota}"

    def save(self, *args, **kwargs):
        if self.grupo_id and not self.pk:
            periodo_grupo = self.grupo.periodo
            if not periodo_grupo or not periodo_grupo.activo:
                raise ValidationError('El ciclo de este grupo ya fue cerrado por el director. No se pueden capturar nuevas calificaciones.')
            self.periodo = periodo_grupo
        super().save(*args, **kwargs)
    
class CierreParcial(models.Model):
    grupo = models.ForeignKey('academic.Grupo', on_delete=models.CASCADE, related_name='cierres_parcial')
    asignatura = models.ForeignKey('academic.Asignatura', on_delete=models.CASCADE, related_name='cierres_parcial')
    parcial = models.PositiveSmallIntegerField()
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cerrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('grupo', 'asignatura', 'parcial')

    def __str__(self):
        return f'Cierre Parcial {self.parcial} — {self.grupo} / {self.asignatura}'
class BoletaParcial(models.Model):
    """Calificación final de un parcial, calculada y guardada por el docente."""
    PARCIALES = [
        (1, 'Primer Parcial'),
        (2, 'Segundo Parcial'),
        (3, 'Tercer Parcial'),
        (4, 'Cuarto Parcial'),
    ]

    alumno     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='boletas_parciales'
    )
    grupo      = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='boletas_parciales')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='boletas_parciales')
    docente    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='boletas_emitidas'
    )
    parcial    = models.IntegerField(choices=PARCIALES)

    # Rubros guardados al momento de publicar
    nota_tareas      = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_actividades = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_asistencia  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_examen      = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota_proyecto    = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notas_extra      = models.JSONField(default=dict, blank=True)   # <- NUEVO: {"clave": nota, ...}
    calificacion_final = models.DecimalField(max_digits=4, decimal_places=2)

    publicada    = models.BooleanField(default=False)  # ← el padre/alumno solo ve si es True
    publicada_en = models.DateTimeField(null=True, blank=True)
    creada_en    = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['alumno', 'grupo', 'asignatura', 'parcial']]
        ordering = ['parcial', 'alumno__last_name']
        verbose_name = 'Boleta Parcial'
        verbose_name_plural = 'Boletas Parciales'

    def __str__(self):
        return f"{self.alumno} — {self.asignatura} P{self.parcial}: {self.calificacion_final}"

class SesionClase(models.Model):
    """
    Sesión de clase en vivo iniciada por un docente.
    Los alumnos del grupo la ven en tiempo real desde la app.
    """

    class Estado(models.TextChoices):
        BORRADOR    = 'borrador', 'Borrador'
        ACTIVA      = 'activa', 'Activa'
        FINALIZADA  = 'finalizada', 'Finalizada'

    docente    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='sesiones_clase',
    )
    grupo      = models.ForeignKey(
        Grupo, on_delete=models.CASCADE,
        related_name='sesiones_clase',
    )
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE,
        related_name='sesiones_clase',
    )
    titulo     = models.CharField(max_length=200)
    estado     = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fecha      = models.DateField(auto_now_add=True)
    creada_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Sesión de Clase'
        verbose_name_plural = 'Sesiones de Clase'
        ordering            = ['-creada_en']

    def __str__(self):
        emoji = {
            self.Estado.BORRADOR: '📝',
            self.Estado.ACTIVA: '🟢',
            self.Estado.FINALIZADA: '🔴',
        }.get(self.estado, '')
        return f"{self.titulo} — {self.grupo} [{emoji} {self.get_estado_display()}]"
class BloqueClase(models.Model):
    """
    Bloque de contenido publicado durante una SesionClase.
    Puede ser texto, PDF, video, imagen, enlace o instrucción de actividad.
    """
    TIPOS = [
        ('texto',     'Texto / Indicación'),
        ('pdf',       'PDF / Documento'),
        ('video',     'Video'),
        ('imagen',    'Imagen'),
        ('link',      'Enlace externo'),
        ('actividad', 'Actividad'),
    ]
 
    sesion    = models.ForeignKey(
        SesionClase, on_delete=models.CASCADE,
        related_name='bloques',
    )
    tipo      = models.CharField(max_length=20, choices=TIPOS)
    titulo    = models.CharField(max_length=200, blank=True)
    contenido = models.TextField()          # texto plano o URL según el tipo
    orden     = models.IntegerField(default=0)
    activo    = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name        = 'Bloque de Clase'
        verbose_name_plural = 'Bloques de Clase'
        ordering            = ['orden', 'creado_en']
 
    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo or self.contenido[:40]}"