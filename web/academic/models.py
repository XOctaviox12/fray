from django.db import models
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from users.models import Plantel  # Asegúrate de que esta importación sea correcta

# ==========================================
# 1. CATALOGOS Y ESTRUCTURA
# ==========================================

class Periodo(models.Model):
    nombre = models.CharField(max_length=50)  # Ej: "Ciclo 2025-2026 A"
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
    # Permitimos nulos para que la migración no falle con los datos viejos
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='grupos', null=True, blank=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, null=True, blank=True)
    
    # Datos del Grupo
    nombre = models.CharField(max_length=50) # Ej: "A", "Matutino"
    grado = models.IntegerField(verbose_name="Grado o Semestre") # 1, 2, 3...
    aula = models.CharField(max_length=50, null=True, blank=True)
    capacidad_maxima = models.IntegerField(default=30)
    
    # Usuarios
    docentes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='grupos_asignados', limit_choices_to={'rol': 'DOCENTE'}, blank=True)
    # Nota: Los alumnos suelen relacionarse con una FK desde el modelo User (User.alumno_grupo), 
    # pero si usas ManyToMany aquí, descomenta la siguiente línea:
    # alumnos = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='grupos_inscritos', limit_choices_to={'rol': 'ALUMNO'}, blank=True)

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
        val = Calificacion.objects.filter(asignatura__grupo=self).aggregate(Avg('nota'))['nota__avg']
        return round(val, 1) if val else 0.0

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
    # Relación con el grupo (mantenemos esto para la instancia específica)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='asignaturas')
    
    # CAMBIO: De ForeignKey a ManyToManyField para múltiples docentes
    docentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        limit_choices_to={'rol': 'DOCENTE'},
        related_name='materias_impartidas'
    )
    
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='asignaturas')
    nombre = models.CharField(max_length=100)
    clave = models.CharField(max_length=20, blank=True, null=True)
    creditos = models.IntegerField(default=0, blank=True, null=True)
    seriacion = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self): 
        return f"{self.nombre} - {self.grupo.grado}º{self.grupo.nombre}"

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