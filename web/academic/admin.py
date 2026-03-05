from django.contrib import admin
from .models import Grupo, Asignatura, Calificacion, Asistencia, Carrera, Periodo, HorarioClase

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
    # 'grupo' ya no existe, usamos 'carrera' o una función personalizada
    list_display = ('nombre', 'carrera', 'mostrar_grupos', 'clave') 
    
    # 'grupo__plantel' ya no funciona porque la relación es ManyToMany
    # Filtramos por carrera o directamente por el plantel de la carrera
    list_filter = ('carrera__plantel', 'carrera', 'docentes')
    
    search_fields = ('nombre', 'clave')

    # Función para mostrar los grupos en la lista del admin
    def mostrar_grupos(self, obj):
        return ", ".join([str(g.nombre) for g in obj.grupos.all()])
    mostrar_grupos.short_description = 'Grupos'

# --- 4. OTROS ---
admin.site.register(Calificacion)
admin.site.register(Asistencia)

admin.site.register(HorarioClase)