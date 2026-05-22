
from django.urls import path
from . import views

urlpatterns = [
    # ── GRUPOS ────────────────────────────────────────────────────────────────
    path('grupos/',                          views.lista_grupos,            name='lista_grupos'),
    path('grupos/nuevo/',                    views.crear_grupo,             name='crear_grupo'),
    path('grupos/detalle/<int:pk>/',         views.detalle_grupo,           name='detalle_grupo'),
    path('grupos/editar/<int:pk>/',          views.editar_grupo,            name='editar_grupo'),
    path('grupos/eliminar/<int:pk>/',        views.eliminar_grupo,          name='eliminar_grupo'),
    path('grupos/horario/<int:grupo_id>/',   views.gestionar_horario_grupo, name='gestionar_horario'),

    # ── ASISTENCIAS ───────────────────────────────────────────────────────────
    path('grupos/<int:grupo_id>/lista/',     views.pasar_lista,             name='pasar_lista'),

    # ── CALIFICACIONES ────────────────────────────────────────────────────────
    path('grupos/<int:grupo_id>/notas/<int:asignatura_id>/',views.registrar_calificaciones,name='registrar_calificaciones'),
    path('grupos/<int:grupo_id>/reporte/',   views.reporte_calificaciones,  name='reporte_calificaciones'),

    # ── ASIGNATURAS ───────────────────────────────────────────────────────────
    path('asignaturas/',                     views.lista_asignaturas,       name='lista_asignaturas'),
    path('asignaturas/crear/',               views.crear_materia,           name='crear_materia'),

    # ── ALUMNOS ───────────────────────────────────────────────────────────────
    path('alumnos/agregar-tutor/',           views.agregar_tutor,           name='agregar_tutor'),
    path('alumno/<int:pk>/editar/',          views.editar_alumno,           name='editar_alumno'),
    path('alumno/<int:pk>/detalle/',         views.detalle_alumno,          name='detalle_alumno'),
    path('alumno/<int:pk>/regenerar-password/', views.regenerar_password,   name='regenerar_password'),

    # ── HORARIOS ──────────────────────────────────────────────────────────────
    path('carga-horaria/',                   views.carga_horaria_alumno,    name='carga_horaria'),
    path('clase/crear/',                     views.crear_clase,             name='crear_clase'),
    path('clase/editar/<int:clase_id>/',     views.editar_clase,            name='editar_clase'),       # ← NUEVO
    path('clase/eliminar/<int:clase_id>/',   views.eliminar_clase,          name='eliminar_clase'),

    # ── API AJAX (opcional, validación server-side en tiempo real) ────────────
    path('api/conflicto/',                   views.api_verificar_conflicto, name='api_verificar_conflicto'),  # ← NUEVO

    # ── PROCESOS ──────────────────────────────────────────────────────────────
    path('promocion-masiva/',                views.promocion_masiva,        name='promocion_masiva'),
    path('actualizar-aulas/',                views.actualizar_aulas,        name='actualizar_aulas'),
]