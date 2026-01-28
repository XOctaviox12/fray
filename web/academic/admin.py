from django.contrib import admin
from .models import Grupo, Asignatura, Calificacion, Asistencia, Carrera, Periodo

# --- 1. NUEVOS MODELOS (CARRERA Y PERIODO) ---
@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'plantel', 'clave_rvoe')
    list_filter = ('plantel', 'nivel')
    search_fields = ('nombre',)

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('activo',)

# --- 2. GRUPO (CORREGIDO) ---
@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    # Eliminamos 'nivel' y ponemos 'carrera'
    list_display = ('nombre', 'grado', 'carrera', 'plantel', 'periodo')
    
    # Filtros actualizados
    list_filter = ('plantel', 'carrera', 'periodo') 
    
    search_fields = ('nombre', 'carrera__nombre')
    autocomplete_fields = ['docentes'] # Opcional, si tienes muchos docentes

# --- 3. ASIGNATURA ---
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo', 'mostrar_docentes', 'creditos')
    list_filter = ('grupo__plantel', 'grupo__carrera')
    search_fields = ('nombre', 'docente__first_name', 'docente__last_name')
    def mostrar_docentes(self, obj):
        # Une los nombres de usuario (o nombres completos) con comas
        return ", ".join([user.username for user in obj.docentes.all()])
    
    # Le damos un nombre bonito a la columna en el Admin
    mostrar_docentes.short_description = 'Docentes'

# --- 4. OTROS ---
admin.site.register(Calificacion)
admin.site.register(Asistencia)