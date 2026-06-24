from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    path('',                    views.login_tutor,      name='login'),
    path('logout/',             views.logout_tutor,     name='logout'),
    path('inicio/',             views.dashboard_tutor,  name='dashboard'),
    path('alumno/<int:pk>/',    views.perfil_alumno,    name='perfil_alumno'),
]