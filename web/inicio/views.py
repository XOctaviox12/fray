from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib.admin.models import LogEntry
import datetime

from .forms import LoginForm
from users.models import User
from academic.models import Periodo, Grupo, Calificacion, Asistencia, Asignatura
from academic.forms import AlumnoForm


def get_campus_theme(user):
    """Configuración visual según el plantel (Colores y Etiquetas)."""
    if not user.plantel:
        return {'color': 'blue', 'labels': {'alumnos': 'Alumnos', 'docentes': 'Docentes', 'grupos': 'Grupos'}}

    es_uni = user.plantel.id == 2
    return {
        'color': 'purple' if es_uni else 'blue',
        'labels': {
            'alumnos':            'Universitarios' if es_uni else 'Alumnos',
            'docentes':           'Catedráticos'   if es_uni else 'Docentes',
            'grupos':             'Facultades'      if es_uni else 'Grupos',
            'descripcion_grupos': 'Carreras y expedientes' if es_uni else 'Grados y secciones escolares',
        }
    }


@login_required
def dashboard_view(request):
    plantel = request.user.plantel
    theme   = get_campus_theme(request.user)
    periodos = Periodo.objects.filter(activo=True)
    hoy      = timezone.now().date()

    # ── Inscripción rápida desde el modal ────────────────────────────
    inscripcion_errors = []
    inscripcion_data   = {}

    if request.method == 'POST' and request.POST.get('accion') == 'inscribir':
        first_name      = request.POST.get('first_name', '').strip()
        last_name       = request.POST.get('last_name',  '').strip()
        email           = request.POST.get('email',      '').strip()
        telefono        = request.POST.get('telefono',   '').strip()
        fecha_nac       = request.POST.get('fecha_nacimiento', '')
        grupo_id        = request.POST.get('grupo', '')

        inscripcion_data = request.POST.dict()

        # Validaciones básicas
        if not first_name:
            inscripcion_errors.append('El nombre es obligatorio.')
        if not last_name:
            inscripcion_errors.append('Los apellidos son obligatorios.')
        if not grupo_id:
            inscripcion_errors.append('Selecciona un grupo de ingreso.')

        if not inscripcion_errors:
            import random, string
            grupo = Grupo.objects.filter(id=grupo_id, plantel=plantel).first()

            if not grupo:
                inscripcion_errors.append('El grupo seleccionado no existe.')
            else:
                # Generar username único
                while True:
                    sufijo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
                    nuevo_username = f"fray{sufijo}"
                    if not User.objects.filter(username=nuevo_username).exists():
                        break

                # Generar contraseña
                password_aleatoria = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                nuevo_alumno = User(
                    username=nuevo_username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email or '',
                    telefono=telefono or None,
                    rol='ALUMNO',
                    plantel=plantel,
                    alumno_grupo=grupo,
                    password_plana=password_aleatoria,
                )
                if fecha_nac:
                    try:
                        from datetime import date
                        nuevo_alumno.fecha_nacimiento = date.fromisoformat(fecha_nac)
                    except ValueError:
                        pass

                nuevo_alumno.set_password(password_aleatoria)
                nuevo_alumno.save()

                messages.success(
                    request,
                    f"✅ Alumno inscrito: {nuevo_alumno.get_full_name()} "
                    f"| Matrícula: {nuevo_alumno.username} "
                    f"| Contraseña: {password_aleatoria}"
                )
                return redirect('dashboard')

    # ── Grupos disponibles para el select del modal ───────────────────
    grupos_disponibles = Grupo.objects.filter(plantel=plantel).prefetch_related('alumnos').order_by('grado', 'nombre')

    # ── Gestión de espacios (Aulas) ───────────────────────────────────
    total_aulas   = getattr(plantel, 'total_aulas', 20)
    aulas_ocupadas = Grupo.objects.filter(plantel=plantel).count()
    aulas_reales  = {'ocupadas': aulas_ocupadas, 'total': total_aulas}

    # ── KPIs ─────────────────────────────────────────────────────────
    total_docentes      = User.objects.filter(plantel=plantel, rol='DOCENTE').count()
    total_coordinadores = User.objects.filter(plantel=plantel, rol='COORD').count()
    total_alumnos       = User.objects.filter(plantel=plantel, rol='ALUMNO').count()

    # ── Asistencia diaria ─────────────────────────────────────────────
    registros_hoy    = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy).count()
    asistencia_global = "Sin registros"
    if registros_hoy > 0:
        presentes = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy, presente=True).count()
        asistencia_global = f"{int((presentes / registros_hoy) * 100)}%"

    # ── Radar de riesgo ───────────────────────────────────────────────
    riesgo_qs      = User.objects.filter(plantel=plantel, rol='ALUMNO', notas__nota__lt=6.0).distinct()
    alumnos_riesgo = riesgo_qs[:5]
    num_riesgo_total = riesgo_qs.count()

    # ── Docentes pendientes ───────────────────────────────────────────
    asignaturas_sin_notas = Asignatura.objects.filter(
        calificaciones__isnull=True, carrera__plantel=plantel
    ).distinct()
    docentes_pendientes = User.objects.filter(id__in=asignaturas_sin_notas).count()

    # ── Actividad reciente ────────────────────────────────────────────
    actividad_reciente = LogEntry.objects.filter(
        user__plantel=plantel
    ).select_related('content_type', 'user').order_by('-action_time')[:5]

    # ── Agenda inteligente ────────────────────────────────────────────
    agenda = []
    if docentes_pendientes > 0:
        agenda.append({'hora': 'URGENTE', 'evento': f'{docentes_pendientes} Docentes con actas pendientes', 'tipo': 'alerta'})
    if num_riesgo_total > 0:
        agenda.append({'hora': 'ATENCIÓN', 'evento': f'{num_riesgo_total} Alumnos bajo el promedio crítico', 'tipo': 'aviso'})
    if aulas_ocupadas >= total_aulas:
        agenda.append({'hora': 'LOGÍSTICA', 'evento': 'Aulas al límite de capacidad', 'tipo': 'alerta'})
    if not agenda:
        agenda.append({'hora': '09:00', 'evento': 'Revisión de expedientes rutinaria', 'tipo': 'rutina'})

    context = {
        'total_docentes':      total_docentes,
        'total_coordinadores': total_coordinadores,
        'total_alumnos':       total_alumnos,
        'asistencia_global':   asistencia_global,
        'periodos':            periodos,
        'alumnos_riesgo':      alumnos_riesgo,
        'docentes_pendientes': docentes_pendientes,
        'agenda':              agenda,
        'actividad_reciente':  actividad_reciente,
        'aulas_reales':        aulas_reales,
        'grupos_disponibles':  grupos_disponibles,
        'inscripcion_errors':  inscripcion_errors,
        'inscripcion_data':    inscripcion_data,
        **theme,
    }

    return render(request, 'inicio/dashboard.html', context)


# ── Autenticación ─────────────────────────────────────────────────────

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login_input = form.cleaned_data.get('username')
            password    = form.cleaned_data.get('password')

            user_obj = User.objects.filter(email=login_input).first()
            username = user_obj.username if user_obj else login_input

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('/admin/' if user.is_superuser else 'dashboard')
            messages.error(request, "Credenciales incorrectas.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Búsqueda global ───────────────────────────────────────────────────

@login_required
def busqueda_global(request):
    query   = request.GET.get('q', '').strip()
    theme   = get_campus_theme(request.user)
    plantel = request.user.plantel

    alumnos  = []
    docentes = []
    grupos   = []

    if query:
        alumnos = User.objects.filter(plantel=plantel, rol='ALUMNO').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)  |
            Q(username__icontains=query)   |
            Q(email__icontains=query)
        )[:10]

        docentes = User.objects.filter(plantel=plantel, rol='DOCENTE').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)  |
            Q(email__icontains=query)
        )[:10]

        grupos = Grupo.objects.filter(plantel=plantel).filter(
            Q(nombre__icontains=query) |
            Q(carrera__nombre__icontains=query)
        )[:10]

    total = len(alumnos) + len(docentes) + len(grupos)

    return render(request, 'inicio/busqueda.html', {
        'query':   query,
        'alumnos': alumnos,
        'docentes': docentes,
        'grupos':  grupos,
        'total':   total,
        **theme,
    })