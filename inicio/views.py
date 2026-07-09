from django.shortcuts import render, redirect,get_object_or_404
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
from users.views import get_campus_theme




@login_required
def dashboard_view(request):
    plantel = request.user.plantel
    theme   = get_campus_theme(request.user)
    periodos = Periodo.objects.filter(activo=True, plantel=request.user.plantel)
    hoy      = timezone.now().date()

    # ── Inscripción rápida desde el modal ────────────────────────────
    inscripcion_errors = []
    inscripcion_data   = {}

    if request.user.rol == 'DOCENTE':
        return redirect('dashboard_docente')
    plantel = request.user.plantel
    
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
                    f"| Contraseña temporal: {password_aleatoria} — Anótala antes de cerrar."
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
        presentes = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy, estado='P').count()
        asistencia_global = f"{int((presentes / registros_hoy) * 100)}%"

    # ── Radar de riesgo ───────────────────────────────────────────────
    riesgo_qs      = User.objects.filter(plantel=plantel, rol='ALUMNO', notas__nota__lt=6.0).distinct()
    alumnos_riesgo = riesgo_qs[:5]
    num_riesgo_total = riesgo_qs.count()

    # ── Docentes pendientes ───────────────────────────────────────────
    asignaturas_sin_notas = Asignatura.objects.filter(
        calificaciones__isnull=True, carrera__plantel=plantel
    ).distinct()
    docentes_pendientes = User.objects.filter(
        rol='DOCENTE',
        plantel=plantel,
        materias_impartidas__in=asignaturas_sin_notas,
    ).distinct().count()

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

def logout_view(request):
    logout(request)
    return redirect('login')

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
                # ── Redirigir según rol ──
                if user.is_superuser:
                    return redirect('/admin/')
                elif user.rol == 'DOCENTE':
                    return redirect('dashboard_docente')
                else:
                    return redirect('dashboard')
            messages.error(request, "Credenciales incorrectas.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


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
@login_required
def dashboard_docente(request):
    if request.user.rol != 'DOCENTE':
        return redirect('dashboard')

    from users.models import DocenteGrupo
    from academic.models import Tarea, ComentarioTarea
    theme = get_campus_theme(request.user)
    hoy   = timezone.now().date()

    # Grupos via DocenteGrupo
    asignaciones = DocenteGrupo.objects.filter(
        docente=request.user, activo=True, asignatura__isnull=False
    ).select_related('grupo', 'asignatura')

    grupos = list({a.grupo for a in asignaciones})

    # KPIs
    registros_hoy = Asistencia.objects.filter(grupo__in=grupos, fecha=hoy).count()
    presentes_hoy = Asistencia.objects.filter(grupo__in=grupos, fecha=hoy, estado='P').count()
    asistencia_hoy = f"{int((presentes_hoy / registros_hoy) * 100)}%" if registros_hoy > 0 else "Sin registro"

    total_alumnos = User.objects.filter(
        rol='ALUMNO', alumno_grupo__in=grupos
    ).distinct().count()

    tareas_activas = Tarea.objects.filter(
        docente=request.user, publicada=True,
        fecha_entrega__gte=timezone.now()
    ).count()

    # Últimas 10 notificaciones: entregas + comentarios
    from academic.models import EntregaTarea, ComentarioTarea, EntregaActividad
    from itertools import chain

    entregas_tarea = EntregaTarea.objects.filter(
        tarea__docente=request.user
    ).select_related('alumno', 'tarea').order_by('-entregada_en')[:10]

    comentarios_tarea = ComentarioTarea.objects.filter(
        tarea__docente=request.user
    ).exclude(autor=request.user).select_related('autor', 'tarea').order_by('-creado_en')[:10]

    # Construir lista unificada de notificaciones
    notificaciones = []

    for e in entregas_tarea:
        notificaciones.append({
            'tipo':   'entrega_tarea',
            'icono':  '📥',
            'color':  '#059669',
            'bg':     '#d1fae5',
            'titulo': f'{e.alumno.get_full_name()} entregó una tarea',
            'sub':    e.tarea.titulo,
            'fecha':  e.entregada_en,
            'url':    f'/docente/tareas/{e.tarea.pk}/',
        })

    for c in comentarios_tarea:
        notificaciones.append({
            'tipo':   'comentario',
            'icono':  '💬',
            'color':  '#7c3aed',
            'bg':     '#ede9fe',
            'titulo': f'{c.autor.get_full_name()} comentó',
            'sub':    c.tarea.titulo,
            'fecha':  c.creado_en,
            'url':    f'/docente/tareas/{c.tarea.pk}/',
        })

    # Ordenar por fecha desc y tomar 10
    notificaciones.sort(key=lambda x: x['fecha'], reverse=True)
    notificaciones = notificaciones[:10]

    return render(request, 'inicio/dashboard_docente.html', {
        'grupos':          grupos,
        'asignaciones':    asignaciones,
        'total_alumnos':   total_alumnos,
        'asistencia_hoy':  asistencia_hoy,
        'tareas_activas':  tareas_activas,
        'notificaciones':  notificaciones,
        'hoy':             hoy,
        **theme,
    })
@login_required
def lista_comunicados(request):
    from academic.models import Comunicado, Grupo
    from django.db.models import Q

    plantel = request.user.plantel

    if request.user.rol == 'DOCENTE':
        # Docente ve: sus propios comunicados + los de directivos que le apliquen
        grupos_docente = Grupo.objects.filter(
            plantel=plantel, docentes=request.user
        )
        comunicados = Comunicado.objects.filter(
            plantel=plantel, activo=True
        ).filter(
            Q(autor=request.user) |
            Q(destinatario='TODOS') |
            Q(destinatario='DOCENTES') |
            Q(destinatario='GRUPO', grupo__in=grupos_docente)
        ).distinct().select_related('autor', 'grupo')
    else:
        # Directivos ven todos los del plantel
        comunicados = Comunicado.objects.filter(
            plantel=plantel, activo=True
        ).select_related('autor', 'grupo')

    # Paginación
    from django.core.paginator import Paginator
    paginator  = Paginator(comunicados, 20)
    page_obj   = paginator.get_page(request.GET.get('page', 1))

    grupos = Grupo.objects.filter(plantel=plantel).order_by('grado', 'nombre')

    return render(request, 'inicio/comunicados.html', {
        'comunicados': page_obj,
        'page_obj':    page_obj,
        'grupos':      grupos,
    })
 
 
@login_required
def crear_comunicado(request):
    from academic.models import Comunicado, Grupo
    import cloudinary.uploader

    plantel      = request.user.plantel
    es_docente   = request.user.rol == 'DOCENTE'
    es_directivo = request.user.rol in ('DIRECTOR', 'COORD', 'ADMIN')

    if not (es_docente or es_directivo):
        messages.error(request, 'No tienes permiso para crear comunicados.')
        return redirect('lista_comunicados')

    # Docentes solo ven sus grupos; directivos ven todos los del plantel
    if es_docente:
        grupos = Grupo.objects.filter(
            plantel=plantel, docentes=request.user
        ).order_by('grado', 'nombre')
    else:
        grupos = Grupo.objects.filter(plantel=plantel).order_by('grado', 'nombre')

    if request.method == 'POST':
        titulo       = request.POST.get('titulo', '').strip()
        cuerpo       = request.POST.get('cuerpo', '').strip()
        destinatario = request.POST.get('destinatario', 'TODOS')
        grupo_id     = request.POST.get('grupo_id') or None
        adjunto_file = request.FILES.get('adjunto')

        # Docentes solo pueden enviar a un grupo específico
        if es_docente:
            destinatario = 'GRUPO'

        if not titulo or not cuerpo:
            messages.error(request, 'El título y el contenido son obligatorios.')
        elif es_docente and not grupo_id:
            messages.error(request, 'Selecciona el grupo destinatario.')
        else:
            grupo = None
            if destinatario == 'GRUPO' and grupo_id:
                grupo = get_object_or_404(grupos, pk=grupo_id)

            comunicado = Comunicado(
                plantel=plantel,
                autor=request.user,
                titulo=titulo,
                cuerpo=cuerpo,
                destinatario=destinatario,
                grupo=grupo,
            )

            if adjunto_file:
                try:
                    resultado = cloudinary.uploader.upload(
                        adjunto_file,
                        folder='fray/comunicados/',
                        resource_type='auto',
                    )
                    comunicado.adjunto = resultado['public_id']
                except Exception as e:
                    messages.warning(request, f'El adjunto no se pudo subir: {e}')

            comunicado.save()
            messages.success(request, f'✅ Comunicado "{titulo}" publicado.')
            return redirect('lista_comunicados')

    return render(request, 'inicio/crear_comunicado.html', {
        'grupos':       grupos,
        'es_docente':   es_docente,
        'es_directivo': es_directivo,
    })
 
 
@login_required
def eliminar_comunicado(request, pk):
    from academic.models import Comunicado
    comunicado = get_object_or_404(Comunicado, pk=pk, plantel=request.user.plantel)
    if request.user.rol not in ('DIRECTOR', 'COORD', 'ADMIN'):
        messages.error(request, 'Sin permiso.')
        return redirect('lista_comunicados')
    if request.method == 'POST':
        comunicado.activo = False
        comunicado.save()
        messages.success(request, 'Comunicado eliminado.')
    return redirect('lista_comunicados')