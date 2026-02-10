from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib.admin.models import LogEntry
import datetime

# Formularios
from .forms import LoginForm

# Modelos
from users.models import User
from academic.models import Periodo, Grupo, Calificacion, Asistencia, Asignatura

def get_campus_theme(user):
    """Configuración visual según el plantel (Colores y Etiquetas)."""
    if not user.plantel:
        return {'color': 'blue', 'labels': {'alumnos': 'Alumnos', 'docentes': 'Docentes', 'grupos': 'Grupos'}}
    
    es_uni = user.plantel.id == 2 # O user.plantel.tipo == 'UNIVERSIDAD'
    return {
        'color': 'purple' if es_uni else 'blue',
        'labels': {
            'alumnos': 'Universitarios' if es_uni else 'Alumnos',
            'docentes': 'Catedráticos' if es_uni else 'Docentes',
            'grupos': 'Facultades' if es_uni else 'Grupos',
            'descripcion_grupos': 'Carreras y expedientes' if es_uni else 'Grados y secciones escolares',
        }
    }

@login_required
def dashboard_view(request):
    plantel = request.user.plantel
    # Obtenemos el tema (colores, labels) según el plantel (Plantel 1 vs Plantel 2)
    theme = get_campus_theme(request.user)
    periodos = Periodo.objects.filter(activo=True)
    hoy = timezone.now().date()

    # --- 1. GESTIÓN DE ESPACIOS (AULAS) ---
    # getattr asegura que si 'total_aulas' no está definido, usemos 20 por defecto
    total_aulas = getattr(plantel, 'total_aulas', 20) 
    aulas_ocupadas = Grupo.objects.filter(plantel=plantel).count()
    
    aulas_reales = {
        'ocupadas': aulas_ocupadas,
        'total': total_aulas
    }

    # --- 2. INDICADORES CLAVE (KPIs) ---
    total_docentes = User.objects.filter(plantel=plantel, rol='DOCENTE').count()
    total_coordinadores = User.objects.filter(plantel=plantel, rol='COORD').count()
    total_alumnos = User.objects.filter(plantel=plantel, rol='ALUMNO').count()

    # --- 3. MÉTRICA DE ASISTENCIA DIARIA ---
    registros_hoy = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy).count()
    asistencia_global = "Sin registros"
    
    if registros_hoy > 0:
        presentes = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy, presente=True).count()
        asistencia_val = (presentes / registros_hoy) * 100
        asistencia_global = f"{int(asistencia_val)}%"

    # --- 4. RADAR DE RIESGO (Promedios < 6.0) ---
    # Filtramos alumnos con al menos una nota reprobatoria
    riesgo_qs = User.objects.filter(
        plantel=plantel, 
        rol='ALUMNO', 
        notas__nota__lt=6.0
    ).distinct()

    alumnos_riesgo = riesgo_qs[:5] # Top 5 para el dashboard
    num_riesgo_total = riesgo_qs.count()

    # --- 5. PENDIENTES DE DOCENTES (Carga de Notas) ---
    # Buscamos asignaturas que aún no tienen ninguna calificación registrada
    asignaturas_sin_notas = Asignatura.objects.filter(
        grupo__plantel=plantel, 
        calificaciones__isnull=True
    ).values_list('docentes', flat=True).distinct() 
    
    docentes_pendientes = User.objects.filter(id__in=asignaturas_sin_notas).count()

    # --- 6. FEED DE ACTIVIDAD RECIENTE ---
    # Obtenemos los últimos logs del admin para este plantel
    actividad_reciente = LogEntry.objects.filter(
        user__plantel=plantel
    ).select_related('content_type', 'user').order_by('-action_time')[:5]

    # --- 7. CONSTRUCCIÓN DE AGENDA INTELIGENTE ---
    agenda = []
    
    # Prioridad Alta: Falta de notas
    if docentes_pendientes > 0:
        agenda.append({
            'hora': 'URGENTE', 
            'evento': f'{docentes_pendientes} Docentes con actas pendientes', 
            'tipo': 'alerta'
        })
    
    # Prioridad Media: Alumnos en riesgo
    if num_riesgo_total > 0:
        agenda.append({
            'hora': 'ATENCIÓN', 
            'evento': f'{num_riesgo_total} Alumnos bajo el promedio crítico', 
            'tipo': 'aviso'
        })
        
    # Prioridad Informativa: Saturación de aulas
    if aulas_ocupadas >= total_aulas:
         agenda.append({
            'hora': 'LOGÍSTICA', 
            'evento': 'Aulas al límite de capacidad', 
            'tipo': 'alerta'
        })

    # Si el día está tranquilo, generamos un evento de rutina
    if not agenda:
        agenda.append({
            'hora': '09:00', 
            'evento': 'Revisión de expedientes rutinaria', 
            'tipo': 'rutina'
        })

    # Empaquetamos todo en el contexto
    context = {
        'total_docentes': total_docentes,
        'total_coordinadores': total_coordinadores,
        'total_alumnos': total_alumnos,
        'asistencia_global': asistencia_global,
        'periodos': periodos,
        'alumnos_riesgo': alumnos_riesgo,
        'docentes_pendientes': docentes_pendientes,
        'agenda': agenda,
        'actividad_reciente': actividad_reciente,
        'aulas_reales': aulas_reales,
        **theme # Desempaqueta colores y labels (alumnos, docentes, etc.)
    }
    
    return render(request, 'inicio/dashboard.html', context)

# --- Vistas de Autenticación ---

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login_input = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Permitir login con email o username
            user_obj = User.objects.filter(email=login_input).first()
            username = user_obj.username if user_obj else login_input
            
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_superuser:
                    return redirect('/admin/')
                return redirect('dashboard')
            messages.error(request, "Credenciales incorrectas.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')