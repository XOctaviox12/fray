# inicio/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('',        views.dashboard_view,    name='dashboard'),
    path('login/',  views.login_view,        name='login'),
    path('logout/', views.logout_view,       name='logout'),
    path('buscar/', views.busqueda_global,   name='busqueda_global'),
    path('comunicados/',              views.lista_comunicados,   name='lista_comunicados'),
    path('comunicados/nuevo/',        views.crear_comunicado,    name='crear_comunicado'),
    path('comunicados/<int:pk>/eliminar/', views.eliminar_comunicado, name='eliminar_comunicado'),
    path('comunicados/<int:pk>/adjunto/', views.ver_adjunto_comunicado, name='ver_adjunto_comunicado'),
    path('en-construccion/', views.en_construccion, name='en_construccion'),
]