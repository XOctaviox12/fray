from django.contrib import admin
from .models import Grupo, Asignatura, Calificacion, Asistencia, Carrera, Periodo, HorarioClase
from .models import SesionClase, BloqueClase

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

class BloqueClaseInline(admin.TabularInline):
    model   = BloqueClase
    extra   = 0
    fields  = ('tipo', 'titulo', 'contenido', 'orden', 'activo')
    ordering = ('orden',)
 
 
@admin.register(SesionClase)
class SesionClaseAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'docente', 'grupo', 'asignatura', 'estado', 'fecha', 'creada_en')
    list_filter   = ('estado', 'grupo', 'asignatura', 'fecha')
    search_fields = ('titulo', 'docente__first_name', 'docente__last_name', 'grupo__nombre')
    readonly_fields = ('creada_en',)
    inlines       = [BloqueClaseInline]
 
    actions = ['terminar_sesiones']
 
    @admin.action(description='Terminar sesiones seleccionadas')
    def terminar_sesiones(self, request, queryset):
        updated = queryset.update(estado=SesionClase.Estado.FINALIZADA)
        self.message_user(request, f'{updated} sesión(es) terminada(s).')
 
 
@admin.register(BloqueClase)
class BloqueClaseAdmin(admin.ModelAdmin):
    list_display  = ('sesion', 'tipo', 'titulo', 'orden', 'activo', 'creado_en')
    list_filter   = ('tipo', 'activo')
    search_fields = ('titulo', 'contenido', 'sesion__titulo')
@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'plantel', 'clave_rvoe')
    list_filter = ('plantel', 'nivel')
    search_fields = ('nombre',)

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plantel', 'tipo', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('activo', 'plantel', 'tipo')

    actions = ['cerrar_ciclo']

    @admin.action(description='Cerrar ciclo y promover alumnos al siguiente semestre')
    def cerrar_ciclo(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecciona un solo periodo a la vez para cerrar.', level=messages.ERROR)
            return

        periodo = queryset.first()

        if not periodo.activo:
            self.message_user(request, f'"{periodo}" ya estaba cerrado.', level=messages.WARNING)
            return

        nuevo_periodo, pendientes = periodo.promover_ciclo()

        self.message_user(
            request,
            f'Ciclo "{periodo}" cerrado. Se creó "{nuevo_periodo}" y se '
            f'promovieron automáticamente los alumnos que no requieren elegir especialidad.',
            level=messages.SUCCESS,
        )

        if pendientes:
            nombres = ", ".join(a.get_full_name() or a.username for a in pendientes)
            self.message_user(
                request,
                f'{len(pendientes)} alumno(s) de 4° necesitan que les asignes '
                f'especialidad a mano antes de entrar a 5°: {nombres}',
                level=messages.WARNING,
            )