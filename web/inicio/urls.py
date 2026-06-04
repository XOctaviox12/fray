from django.urls import path, include
from . import views

urlpatterns = [
    path('',                views.dashboard_view,     name='dashboard'),
    path('docente/',        views.dashboard_docente,  name='dashboard_docente'), 
    path('login/',          views.login_view,         name='login'),
    path('logout/',         views.logout_view,        name='logout'),
    path('buscar/',         views.busqueda_global,    name='busqueda_global'),
    path('docente/',        include('docente.urls', )),
]