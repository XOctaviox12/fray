# web/inicio/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Si alguien entra a la raíz '/', ve el dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Rutas de sesión
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]