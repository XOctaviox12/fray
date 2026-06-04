# docente/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Mi Espacio
    path('grupos/',              views.mis_grupos,           name='docente_mis_grupos'),
    path('horario/',             views.mi_horario,           name='docente_horario'),

    # Clase
    path('asistencia/',          views.lista_asistencia,     name='docente_lista_asistencia'),
    path('tareas/',                      views.tareas,         name='docente_tareas'),
    path('tareas/crear/',                views.crear_tarea,    name='crear_tarea'),
    path('tareas/<int:pk>/',             views.detalle_tarea,  name='detalle_tarea'),
    path('tareas/<int:pk>/eliminar/',    views.eliminar_tarea, name='eliminar_tarea'),
    path('actividades/',         views.actividades,          name='docente_actividades'),

    # Calificaciones
    path('calificar/tareas/',    views.calificar_tareas,     name='docente_calificar_tareas'),
    path('calificar/actividades/', views.calificar_actividades, name='docente_calificar_actividades'),
    path('boleta/',              views.boleta,               name='docente_boleta'),

    # Contenido
    path('material/',            views.material_apoyo,       name='docente_material'),
    path('contenido/',           views.subir_contenido,      name='docente_contenido'),
]