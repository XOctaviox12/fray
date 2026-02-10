from django.urls import path
from . import views  

urlpatterns = [
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/nuevo/', views.crear_grupo, name='crear_grupo'),
    path('grupos/detalle/<int:pk>/', views.detalle_grupo, name='detalle_grupo'), 
    path('grupos/editar/<int:pk>/', views.editar_grupo, name='editar_grupo'),
    path('grupos/eliminar/<int:pk>/', views.eliminar_grupo, name='eliminar_grupo'),
    path('promocion-masiva/', views.promocion_masiva, name='promocion_masiva'),
    path('actualizar-aulas/', views.actualizar_aulas, name='actualizar_aulas'),
    path('asingnaturas/', views.lista_asignaturas, name='lista_asignatura'),
    path('asingnaturas/crear-asignatura', views.crear_materia, name='crear-materia'),
    path('alumnos/agregar-tutor/', views.agregar_tutor, name='agregar_tutor'),
]