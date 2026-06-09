# inicio/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('',        views.dashboard_view,    name='dashboard'),
    path('login/',  views.login_view,        name='login'),
    path('logout/', views.logout_view,       name='logout'),
    path('buscar/', views.busqueda_global,   name='busqueda_global'),
    # ← dashboard_docente se eliminó de aquí, vive en docente/urls.py
]