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
    path('ver-pdf/<int:pk>/<str:tipo>/', views.ver_pdf, name='ver_pdf'),
    path('tareas/crear/',                views.crear_tarea,    name='crear_tarea'),
    path('tareas/<int:pk>/',             views.detalle_tarea,  name='detalle_tarea'),
    path('tareas/<int:pk>/eliminar/',    views.eliminar_tarea, name='eliminar_tarea'),
    path('tareas/<int:pk>/editar/', views.editar_tarea, name='editar_tarea'),

    #actividades
    path('actividades/',         views.actividades,          name='docente_actividades'),
    path('actividades/crear/',              views.crear_actividad,     name='crear_actividad'),
    path('actividades/<int:pk>/',           views.detalle_actividad,   name='detalle_actividad'),
    path('actividades/<int:pk>/eliminar/',  views.eliminar_actividad,  name='eliminar_actividad'),
    path('actividades/<int:pk>/editar/',   views.editar_actividad,  name='editar_actividad'),

    # Calificaciones
    path('calificar/tareas/',    views.calificar_tareas,     name='docente_calificar_tareas'),
    path('calificar/actividades/', views.calificar_actividades, name='docente_calificar_actividades'),
    # Boleta y concentrado
    path('boleta/',                          views.boleta,              name='docente_boleta'),
    path('boleta/<int:grupo_id>/',           views.boleta_grupo,        name='docente_boleta_grupo'),
    path('concentrado/',                     views.concentrado,         name='docente_concentrado'),

    # Contenido
    path('material/',                       views.material_apoyo,     name='material_apoyo'),
    path('material/subir/',                 views.subir_material,      name='subir_material'),
    path('material/<int:pk>/',              views.detalle_material,    name='detalle_material'),
    path('material/<int:pk>/eliminar/',     views.eliminar_material,   name='eliminar_material'),
    path('material/carpeta/<int:pk>/eliminar/', views.eliminar_carpeta, name='eliminar_carpeta'),
    path('material/reordenar/',             views.reordenar_material,  name='reordenar_material'),
    path('material/carpetas/reordenar/',    views.reordenar_carpetas,  name='reordenar_carpetas'),

    path('material/carpetas/json/', views.carpetas_json, name='carpetas_json'),


]