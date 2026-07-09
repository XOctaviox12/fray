# docente/urls.py — CORREGIDO
from django.urls import path
from . import views

urlpatterns = [
    # ── Dashboard docente ─────────────────────────────────────────────────────
    path('',                             views.dashboard_docente,    name='dashboard_docente'),

    # ── Mi Espacio ────────────────────────────────────────────────────────────
    path('grupos/',                      views.mis_grupos,           name='docente_mis_grupos'),
    path('horario/',                     views.mi_horario,           name='docente_horario'),

    # ── Asistencia ────────────────────────────────────────────────────────────
    path('asistencia/',                  views.lista_asistencia,     name='docente_lista_asistencia'),

    # ── Tareas ────────────────────────────────────────────────────────────────
    path('tareas/',                      views.tareas,               name='docente_tareas'),
    path('tareas/crear/',                views.crear_tarea,          name='crear_tarea'),
    path('tareas/<int:pk>/',             views.detalle_tarea,        name='detalle_tarea'),
    path('tareas/<int:pk>/editar/',      views.editar_tarea,         name='editar_tarea'),
    path('tareas/<int:pk>/eliminar/',    views.eliminar_tarea,       name='eliminar_tarea'),

    # ── Actividades ───────────────────────────────────────────────────────────
    path('actividades/',                 views.actividades,              name='docente_actividades'),
    path('actividades/crear/',           views.crear_actividad,          name='crear_actividad'),
    path('actividades/<int:pk>/',        views.detalle_actividad,        name='detalle_actividad'),
    path('actividades/<int:pk>/editar/', views.editar_actividad,         name='editar_actividad'),
    path('actividades/<int:pk>/eliminar/', views.eliminar_actividad,     name='eliminar_actividad'),

    # ── Calificaciones ────────────────────────────────────────────────────────
    path('calificar/tareas/',            views.calificar_tareas,         name='docente_calificar_tareas'),
    path('calificar/actividades/',       views.calificar_actividades,    name='docente_calificar_actividades'),
    path('boleta/', views.boleta, name='docente_boleta_lista'),
    path('boleta/<int:grupo_id>/<int:asignatura_id>/', views.boleta_grupo, name='docente_boleta_grupo'),
    path('concentrado/',                 views.concentrado,              name='docente_concentrado'),

    # ── Material de Apoyo ─────────────────────────────────────────────────────
    path('material/',                    views.material_apoyo,           name='material_apoyo'),
    path('material/subir/',              views.subir_material,           name='subir_material'),
    path('material/<int:pk>/',           views.detalle_material,         name='detalle_material'),
    path('material/<int:pk>/eliminar/',  views.eliminar_material,        name='eliminar_material'),
    path('material/carpeta/<int:pk>/eliminar/', views.eliminar_carpeta,  name='eliminar_carpeta'),
    path('material/reordenar/',          views.reordenar_material,       name='reordenar_material'),
    path('material/carpetas/reordenar/', views.reordenar_carpetas,       name='reordenar_carpetas'),
    path('material/carpetas/json/',      views.carpetas_json,            name='carpetas_json'),

    # ── Planificación ─────────────────────────────────────────────────────────
    path('planes/',                      views.lista_planes,             name='docente_lista_planes'),
    path('planes/nuevo/',                views.crear_plan,               name='docente_crear_plan'),
    path('planes/<int:pk>/',             views.detalle_plan,             name='docente_detalle_plan'),
    path('planes/<int:pk>/editar/',      views.editar_plan,              name='docente_editar_plan'),
    path('planes/<int:pk>/eliminar/',    views.eliminar_plan,            name='docente_eliminar_plan'),

    # ── Utilidades ────────────────────────────────────────────────────────────
    path('ver-pdf/<int:pk>/<str:tipo>/', views.ver_pdf,                  name='ver_pdf'),

    # ── PDFs — prefijos distintos para evitar conflicto de rutas ─────────────
    path('pdf/boleta-alumno/<int:alumno_pk>/',              views.pdf_boleta_alumno,   name='pdf_boleta_alumno'),
    path('pdf/boleta-grupo/<int:grupo_id>/',                views.pdf_boleta_grupo,    name='pdf_boleta_grupo'),
    path('pdf/concentrado/<int:grupo_id>/',                 views.pdf_concentrado,     name='pdf_concentrado'),
    path('pdf/asistencia-grupo/<int:grupo_pk>/',            views.pdf_asistencia_grupo,name='pdf_asistencia_grupo'),
    path('pdf/asistencia/<int:grupo_id>/<int:asignatura_id>/', views.pdf_asistencia,  name='pdf_asistencia'),
    path('pdf/cronograma/<int:plan_pk>/',                   views.pdf_cronograma,      name='pdf_cronograma'),
    
    # Calificación parcial
    path('parcial/',                              views.parcial,              name='docente_parcial'),
    path('parcial/<int:grupo_id>/<int:asig_id>/', views.parcial_detalle,      name='docente_parcial_detalle'),
    path('parcial/<int:grupo_id>/<int:asig_id>/config/', views.parcial_config, name='docente_parcial_config'),
]