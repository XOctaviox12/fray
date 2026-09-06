from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    path('',                    views.login_tutor,      name='login'),
    path('logout/',             views.logout_tutor,     name='logout'),
    path('inicio/',             views.dashboard_tutor,  name='dashboard'),
    path('alumno/<int:alumno_id>/', views.perfil_alumno, name='perfil_alumno'),
    # tutor/urls.py
    path('actualizar/', views.dashboard_tutor_actualizar, name='dashboard_actualizar'),
]