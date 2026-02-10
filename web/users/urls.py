# web/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    
    path('perfil/', views.perfil_view, name='perfil'), 
    
    # Rutas para la gestión de coordinadores
    path('coordinadores/', views.lista_coordinadores, name='lista_coordinadores'),
    path('coordinadores/nuevo/', views.crear_coordinador, name='crear_coordinador'),
    path('coordinadores/editar/<int:pk>/', views.editar_coordinador, name='editar_coordinador'),
    path('coordinadores/eliminar/<int:pk>/', views.eliminar_coordinador, name='eliminar_coordinador'),
    path('coordinadores/detalle/<int:pk>/', views.detalle_coordinador, name='detalle_coordinador'),
    
    # Rutas de administración inicial
    path('plantel/nuevo/', views.crear_plantel, name='crear_plantel'),
    path('director/nuevo/', views.crear_director, name='crear_director'),
    path('alumno/registro/', views.register_alumno, name='register_alumno'),

    path('docentes/', views.lista_docentes, name='lista_docentes'),
    path('docentes/nuevo/', views.crear_docente, name='crear_docente'),
    path('docentes/detalle/<int:pk>/', views.detalle_docente, name='detalle_docente'),
    path('docentes/editar/<int:pk>/', views.editar_docente, name='editar_docente'),
    path('docentes/eliminar/<int:pk>/', views.eliminar_docente, name='eliminar_docente'),
]