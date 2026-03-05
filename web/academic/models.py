from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from users.models import Plantel 
from django.core.exceptions import ValidationError

# ==========================================
# 1. CATALOGOS Y ESTRUCTURA
# ==========================================

class Periodo(models.Model):
    nombre = models.CharField(max_length=50)  
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self): 
        return self.nombre

class Carrera(models.Model):
    """
    Define el Programa Educativo. 
    En Básica: "Secundaria General", "Bachillerato Tecnológico".
    En Uni: "Lic. en Derecho", "Ing. Software".
    """
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    nivel = models.CharField(max_length=20, choices=[
        ('SECUNDARIA', 'Secundaria'),
        ('PREPARATORIA', 'Preparatoria'),
        ('UNIVERSIDAD', 'Universidad'),
    ])
    clave_rvoe = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.nivel})"

# ==========================================
# 2. GRUPOS (La clase física con alumnos)
# ==========================================

class Grupo(models.Model):
    # Relaciones Jerárquicas
    plantel = models.ForeignKey(Plantel, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='grupos', null=True, blank=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, null=True, blank=True)
    
    # Datos del Grupo
    nombre = models.CharField(max_length=50) # Ej: "A", "Matutino"
    grado = models.IntegerField(verbose_name="Grado o Semestre") # 1, 2, 3...
    aula = models.CharField(max_length=50, null=True, blank=True)
    capacidad_maxima = models.IntegerField(default=30)
    
    # Usuarios
    docentes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='grupos_asignados', limit_choices_to={'rol': 'DOCENTE'}, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['grado', 'nombre']

    def __str__(self):
        return f"{self.carrera.nombre} - {self.grado}º {self.nombre}"

    # --- PROPERTIES (KPIs) ---
    @property
    def ocupacion_porcentaje(self):
        if self.capacidad_maxima > 0:
            # CAMBIA self.user_set.count() por self.alumnos.count()
            return (self.alumnos.count() / self.capacidad_maxima) * 100
        return 0

    @property
    def promedio_general(self):
        from .models import Calificacion
        from django.db.models import Avg

        # CAMBIO: Usamos 'asignatura__grupos' (en plural) y agregamos .distinct()
        val = Calificacion.objects.filter(
            asignatura__grupos=self 
        ).distinct().aggregate(Avg('nota'))['nota__avg']
        
        return val or 0.0

    @property
    def asistencia_mensual(self):
        now = timezone.now()
        total = Asistencia.objects.filter(grupo=self, fecha__month=now.month).count()
        if total == 0: return 0
        presentes = Asistencia.objects.filter(grupo=self, fecha__month=now.month, presente=True).count()
        return int((presentes / total) * 100)
    
    def __str__(self):
        # CORRECCIÓN DE SEGURIDAD:
        # Si tiene carrera, usamos su nombre. Si no, ponemos "General".
        nombre_carrera = self.carrera.nombre if self.carrera else "General"
        return f"{nombre_carrera} - {self.grado}º {self.nombre}"

# ==========================================
# 3. ACADÉMICO (Materias y Notas)
# ==========================================

class Asignatura(models.Model):
    # Relación ManyToMany con Grupo (usamos 'asignaturas' para el template)
    grupos = models.ManyToManyField(
        Grupo, 
        related_name='asignaturas', 
        verbose_name="Grupos"
    )
    
    # Relación con Carrera (Cambiamos el related_name para que no choque)
    carrera = models.ForeignKey(
        Carrera, 
        on_delete=models.CASCADE, 
        related_name='asignaturas_de_carrera'
    )
    
    # Docentes (ManyToMany)
    docentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='materias_impartidas'
    )
    
    nombre = models.CharField(max_length=100)
    clave = models.CharField(max_length=20, blank=True, null=True)
    creditos = models.IntegerField(default=0, blank=True, null=True)
    seriacion = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self): 
        return self.nombre

class Calificacion(models.Model):
    alumno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notas')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='calificaciones')
    nota = models.DecimalField(max_digits=4, decimal_places=2) # 0.00 a 10.00
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.alumno} - {self.asignatura}: {self.nota}"

class Asistencia(models.Model):
    alumno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    presente = models.BooleanField(default=True)


class HorarioClase(models.Model):
    DIAS_SEMANA = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
    ]

    asignatura = models.ForeignKey('Asignatura', on_delete=models.CASCADE, related_name='horarios')
    maestro = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'rol': 'MAESTRO'})
    grupo = models.ForeignKey('Grupo', on_delete=models.CASCADE, related_name='horarios')
    dia = models.CharField(max_length=2, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    aula = models.CharField(max_length=50, default="Por definir")
    
    # Nuevo: Para controlar ciclos escolares
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de Clase"
        verbose_name_plural = "Horarios de Clases"
        ordering = ['dia', 'hora_inicio']

    def __str__(self):
        return f"{self.asignatura.nombre} | {self.get_dia_display()} {self.hora_inicio}"

    def clean(self):
        """Validaciones de integridad de horarios"""
        
        # 1. Validar que la hora de fin sea después de la de inicio
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError({'hora_fin': 'La hora de fin debe ser posterior a la de inicio.'})

        # 2. Validar colisión de MAESTRO (¿El maestro ya tiene clase a esa hora?)
        maestro_ocupado = HorarioClase.objects.filter(
            dia=self.dia,
            maestro=self.maestro,
            activo=True,
            hora_inicio__lt=self.hora_fin,
            hora_fin__gt=self.hora_inicio
        ).exclude(pk=self.pk)
        
        if maestro_ocupado.exists():
            clase = maestro_ocupado.first()
            raise ValidationError(f'El maestro ya tiene la clase de {clase.asignatura} asignada en este horario.')

        # 3. Validar colisión de GRUPO (¿El grupo ya tiene otra materia a esa hora?)
        grupo_ocupado = HorarioClase.objects.filter(
            dia=self.dia,
            grupo=self.grupo,
            activo=True,
            hora_inicio__lt=self.hora_fin,
            hora_fin__gt=self.hora_inicio
        ).exclude(pk=self.pk)

        if grupo_ocupado.exists():
            raise ValidationError(f'Este grupo ya tiene una materia asignada los {self.get_dia_display()} a esta hora.')

        # 4. Validar colisión de AULA (¿El salón está ocupado?)
        if self.aula != "Por definir":
            aula_ocupada = HorarioClase.objects.filter(
                dia=self.dia,
                aula=self.aula,
                activo=True,
                hora_inicio__lt=self.hora_fin,
                hora_fin__gt=self.hora_inicio
            ).exclude(pk=self.pk)

            if aula_ocupada.exists():
                raise ValidationError(f'El aula {self.aula} ya está ocupada en este horario.')

    def save(self, *args, **kwargs):
        self.full_clean() # Forzar validaciones antes de guardar
        super().save(*args, **kwargs)