from django.urls import path
from . import views
 
urlpatterns = [
    # GRUPOS
    path('grupos/',                              views.lista_grupos,          name='lista_grupos'),
    path('grupos/nuevo/',                        views.crear_grupo,           name='crear_grupo'),
    path('grupos/detalle/<int:pk>/',             views.detalle_grupo,         name='detalle_grupo'),
    path('grupos/editar/<int:pk>/',              views.editar_grupo,          name='editar_grupo'),
    path('grupos/eliminar/<int:pk>/',            views.eliminar_grupo,        name='eliminar_grupo'),
    path('grupos/horario/<int:grupo_id>/',       views.gestionar_horario_grupo, name='gestionar_horario'),
 
    # ASIGNATURAS
    path('asignaturas/',                         views.lista_asignaturas,     name='lista_asignaturas'),
    path('asignaturas/crear/',                   views.crear_materia,         name='crear_materia'),
 
    # ALUMNOS Y TUTORES
    path('alumnos/agregar-tutor/',               views.agregar_tutor,         name='agregar_tutor'),
    path('alumno/<int:pk>/detalle/',             views.detalle_alumno,        name='detalle_alumno'),     # ← ahora función, no clase
    path('alumno/<int:pk>/regenerar-password/',  views.regenerar_password,    name='regenerar_password'),
 
    # HORARIOS
    path('carga-horaria/',                       views.carga_horaria_alumno,  name='carga_horaria'),
    path('clase/crear/',                         views.crear_clase,           name='crear_clase'),
    path('clase/eliminar/<int:clase_id>/',       views.eliminar_clase,        name='eliminar_clase'),     # ← FALTABA
 
    # PROCESOS ACADÉMICOS
    path('promocion-masiva/',                    views.promocion_masiva,      name='promocion_masiva'),
    path('actualizar-aulas/',                    views.actualizar_aulas,      name='actualizar_aulas'),
]