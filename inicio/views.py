from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib.admin.models import LogEntry
from urllib.parse import urlparse
import datetime
import secrets
import string
from django.urls import reverse
from .forms import LoginForm
from users.models import User
from academic.models import Periodo, Grupo, Calificacion, Asistencia, Asignatura
from academic.forms import AlumnoForm
from users.views import get_campus_theme
from academic.models import Periodo
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging


logger = logging.getLogger(__name__)

# ─── Constantes de seguridad ────────────────────────────────────────────────
BUSQUEDA_MAX_LEN = 100                     # evita queries gigantes / DoS leve
ADJUNTO_MAX_SIZE = 10 * 1024 * 1024        # 10 MB
ADJUNTO_EXTENSIONES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf'}
ADJUNTO_HOSTS_PERMITIDOS = {'res.cloudinary.com'}  # allowlist anti-SSRF


def _plantel_del_usuario(request):
    """Devuelve el plantel del usuario o None. Centraliza esta lectura para
    que ninguna vista filtre accidentalmente con plantel=None sin darse cuenta."""
    return getattr(request.user, 'plantel', None)


@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('/admin/')

    if request.user.rol == 'DOCENTE':
        return redirect('dashboard_docente')

    plantel = _plantel_del_usuario(request)
    if not plantel:
        messages.error(request, 'Tu cuenta no tiene un plantel asignado. Contacta al administrador.')
        return redirect('login')

    theme = get_campus_theme(request.user)
    periodos = Periodo.objects.filter(activo=True, plantel=plantel)
    periodo_actual = periodos.first()
    hoy = timezone.now().date()

    # ── Inscripción rápida desde el modal ────────────────────────────
    inscripcion_errors = []
    inscripcion_data = {}

    if request.method == 'POST' and request.POST.get('accion') == 'inscribir':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        fecha_nac = request.POST.get('fecha_nacimiento', '')
        grupo_id = request.POST.get('grupo', '')

        inscripcion_data = request.POST.dict()

        # Validaciones básicas
        if not first_name:
            inscripcion_errors.append('El nombre es obligatorio.')
        if not last_name:
            inscripcion_errors.append('Los apellidos son obligatorios.')
        if not grupo_id:
            inscripcion_errors.append('Selecciona un grupo de ingreso.')

        # grupo_id debe ser numérico antes de tocar la BD
        grupo_id_valido = None
        if grupo_id:
            try:
                grupo_id_valido = int(grupo_id)
            except (TypeError, ValueError):
                inscripcion_errors.append('El grupo seleccionado no es válido.')

        # Validar formato de email si se proporcionó
        if email:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                inscripcion_errors.append('El correo electrónico no tiene un formato válido.')

        fecha_nac_parsed = None
        if fecha_nac:
            try:
                fecha_nac_parsed = datetime.date.fromisoformat(fecha_nac)
            except ValueError:
                inscripcion_errors.append('La fecha de nacimiento no tiene un formato válido.')

        if not inscripcion_errors:
            # El filtro plantel=plantel evita inscribir en un grupo de OTRO
            # plantel aunque alguien manipule grupo_id manualmente en el POST.
            grupo = Grupo.objects.filter(id=grupo_id_valido, plantel=plantel).first()

            if not grupo:
                inscripcion_errors.append('El grupo seleccionado no existe.')
            else:
                # Generar username único
                while True:
                    sufijo = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(5))
                    nuevo_username = f"fray{sufijo}"
                    if not User.objects.filter(username=nuevo_username).exists():
                        break

                # secrets.choice es criptográficamente seguro; random.choices NO lo es
                # y nunca debe usarse para generar credenciales.
                password_aleatoria = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

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
                if fecha_nac_parsed:
                    nuevo_alumno.fecha_nacimiento = fecha_nac_parsed

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
    grupos_disponibles = Grupo.objects.filter(plantel=plantel).select_related('carrera').prefetch_related('alumnos').order_by('carrera__nombre', 'grado', 'nombre')

    # ── Gestión de espacios (Aulas) ───────────────────────────────────
    total_aulas = getattr(plantel, 'total_aulas', 20)
    aulas_ocupadas = Grupo.objects.filter(plantel=plantel).count()
    aulas_reales = {'ocupadas': aulas_ocupadas, 'total': total_aulas}

    # ── KPIs ─────────────────────────────────────────────────────────
    total_docentes = User.objects.filter(plantel=plantel, rol='DOCENTE').count()
    total_coordinadores = User.objects.filter(plantel=plantel, rol='COORD').count()
    total_alumnos = User.objects.filter(plantel=plantel, rol='ALUMNO').count()

    # ── Asistencia diaria ─────────────────────────────────────────────
    registros_hoy = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy).count()
    asistencia_global = "Sin registros"
    if registros_hoy > 0:
        presentes = Asistencia.objects.filter(grupo__plantel=plantel, fecha=hoy, estado='P').count()
        asistencia_global = f"{int((presentes / registros_hoy) * 100)}%"

    # ── Radar de riesgo ───────────────────────────────────────────────
    riesgo_qs = User.objects.filter(plantel=plantel, rol='ALUMNO', notas__nota__lt=6.0).distinct()
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
        'grupos_disponibles': grupos_disponibles,
        'inscripcion_errors': inscripcion_errors,
        'inscripcion_data': inscripcion_data,
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
            password = form.cleaned_data.get('password')

            user_obj = User.objects.filter(email=login_input).first()
            username = user_obj.username if user_obj else login_input

            user = authenticate(request, username=username, password=password)
            if user:
                if user.rol == 'ALUMNO':
                    form.add_error(None, "Los alumnos deben usar la app móvil para iniciar sesión.")
                else:
                    login(request, user)
                    if user.is_superuser:
                        return redirect('/admin/')
                    elif user.rol == 'DOCENTE':
                        return redirect('dashboard_docente')
                    else:
                        return redirect('dashboard')
            else:
                # Mensaje genérico: no reveles si el usuario/email existe o no,
                # evita que alguien use el login para enumerar cuentas válidas.
                form.add_error(None, "Credenciales incorrectas.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


# ── Búsqueda (vista de página completa) ─────────────────────────────────
# NOTA: esta función hace lo mismo que buscar_global (AJAX) pero renderiza
# una plantilla en vez de devolver JSON. Si ya no la usa ninguna ruta,
# considera eliminarla para no mantener dos implementaciones del mismo
# filtro de seguridad por separado.

@login_required
def busqueda_global(request):
    query = request.GET.get('q', '').strip()[:BUSQUEDA_MAX_LEN]
    theme = get_campus_theme(request.user)
    plantel = _plantel_del_usuario(request)

    alumnos = []
    docentes = []
    grupos = []

    if query and plantel:
        alumnos = User.objects.filter(plantel=plantel, rol='ALUMNO').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )[:10]

        docentes = User.objects.filter(plantel=plantel, rol='DOCENTE').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:10]

        grupos = Grupo.objects.filter(plantel=plantel).filter(
            Q(nombre__icontains=query) |
            Q(carrera__nombre__icontains=query)
        )[:10]

    total = len(alumnos) + len(docentes) + len(grupos)

    return render(request, 'inicio/busqueda.html', {
        'query': query,
        'alumnos': alumnos,
        'docentes': docentes,
        'grupos': grupos,
        'total': total,
        **theme,
    })


@login_required
def dashboard_docente(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    if request.user.rol != 'DOCENTE':
        return redirect('dashboard')

    from users.models import DocenteGrupo
    from academic.models import Tarea, ComentarioTarea

    theme = get_campus_theme(request.user)
    hoy = timezone.now().date()

    # Ya filtrado por docente=request.user: un docente solo ve sus propios grupos.
    asignaciones = DocenteGrupo.objects.filter(
        docente=request.user, activo=True, asignatura__isnull=False
    ).select_related('grupo', 'asignatura')

    grupos = list({a.grupo for a in asignaciones})

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

    # Ambas consultas ya filtran por tarea__docente=request.user: un docente
    # nunca ve entregas/comentarios de tareas de otro docente.
    from academic.models import EntregaTarea, ComentarioTarea, EntregaActividad

    entregas_tarea = EntregaTarea.objects.filter(
        tarea__docente=request.user
    ).select_related('alumno', 'tarea').order_by('-entregada_en')[:10]

    comentarios_tarea = ComentarioTarea.objects.filter(
        tarea__docente=request.user
    ).exclude(autor=request.user).select_related('autor', 'tarea').order_by('-creado_en')[:10]

    notificaciones = []

    for e in entregas_tarea:
        notificaciones.append({
            'tipo': 'entrega_tarea',
            'icono': '📥',
            'color': '#059669',
            'bg': '#d1fae5',
            'titulo': f'{e.alumno.get_full_name()} entregó una tarea',
            'sub': e.tarea.titulo,
            'fecha': e.entregada_en,
            'url': f'/docente/tareas/{e.tarea.pk}/',
        })

    for c in comentarios_tarea:
        notificaciones.append({
            'tipo': 'comentario',
            'icono': '💬',
            'color': '#7c3aed',
            'bg': '#ede9fe',
            'titulo': f'{c.autor.get_full_name()} comentó',
            'sub': c.tarea.titulo,
            'fecha': c.creado_en,
            'url': f'/docente/tareas/{c.tarea.pk}/',
        })

    notificaciones.sort(key=lambda x: x['fecha'], reverse=True)
    notificaciones = notificaciones[:10]

    return render(request, 'inicio/dashboard_docente.html', {
        'grupos': grupos,
        'asignaciones': asignaciones,
        'total_alumnos': total_alumnos,
        'asistencia_hoy': asistencia_hoy,
        'tareas_activas': tareas_activas,
        'notificaciones': notificaciones,
        'hoy': hoy,
        **theme,
    })


@login_required
def lista_comunicados(request):
    from academic.models import Comunicado, Grupo

    plantel = _plantel_del_usuario(request)
    if not plantel:
        messages.error(request, 'Tu cuenta no tiene un plantel asignado.')
        return redirect('dashboard')

    if request.user.rol == 'DOCENTE':
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
        ).exclude(
            Q(publico__in=['ALUMNOS', 'PADRES']) & ~Q(autor=request.user)
        ).distinct().select_related('autor', 'grupo')
    else:
        comunicados = Comunicado.objects.filter(
            plantel=plantel, activo=True
        ).select_related('autor', 'grupo')

    from django.core.paginator import Paginator
    paginator = Paginator(comunicados, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    grupos = Grupo.objects.filter(plantel=plantel).order_by('grado', 'nombre')

    return render(request, 'inicio/comunicados.html', {
        'comunicados': page_obj,
        'page_obj': page_obj,
        'grupos': grupos,
    })


@login_required
def crear_comunicado(request):
    from academic.models import Comunicado, Grupo, Asignatura
    import cloudinary.uploader

    plantel = _plantel_del_usuario(request)
    if not plantel:
        messages.error(request, 'Tu cuenta no tiene un plantel asignado.')
        return redirect('lista_comunicados')

    es_docente = request.user.rol == 'DOCENTE'
    es_directivo = request.user.rol in ('DIRECTOR', 'COORD', 'ADMIN')

    if not (es_docente or es_directivo):
        messages.error(request, 'No tienes permiso para crear comunicados.')
        return redirect('lista_comunicados')

    if es_docente:
        asignaturas = Asignatura.objects.filter(
            carrera__plantel=plantel, docentes=request.user
        ).distinct().order_by('nombre')
    else:
        asignaturas = Asignatura.objects.filter(carrera__plantel=plantel).order_by('nombre')

    if es_docente:
        grupos_base = Grupo.objects.filter(
            plantel=plantel, docentes=request.user, periodo__activo=True
        )
    else:
        grupos_base = Grupo.objects.filter(plantel=plantel, periodo__activo=True)

    grupos = grupos_base.prefetch_related('asignaturas').order_by('grado', 'nombre').distinct()

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        cuerpo = request.POST.get('cuerpo', '').strip()
        destinatario = request.POST.get('destinatario', 'TODOS')
        publico = request.POST.get('publico', 'AMBOS')
        asignatura_id = request.POST.get('asignatura_id') or None
        grupo_ids = request.POST.getlist('grupo_ids')
        adjunto_file = request.FILES.get('adjunto')

        if es_docente:
            destinatario = 'GRUPO'

        if destinatario == 'DOCENTES':
            publico = 'AMBOS'

        asignatura = None
        if asignatura_id:
            asignatura = Asignatura.objects.filter(pk=asignatura_id, carrera__plantel=plantel).first()

        contexto_error = {
            'grupos': grupos, 'asignaturas': asignaturas,
            'es_docente': es_docente, 'es_directivo': es_directivo,
        }

        if not titulo or not cuerpo:
            messages.error(request, 'El título y el contenido son obligatorios.')
            return render(request, 'inicio/crear_comunicado.html', contexto_error)

        if destinatario == 'GRUPO' and not grupo_ids:
            messages.error(request, 'Selecciona al menos un grupo destinatario.')
            return render(request, 'inicio/crear_comunicado.html', contexto_error)

        # ── Validar el adjunto ANTES de subirlo a Cloudinary ──────────
        if adjunto_file:
            nombre_archivo = adjunto_file.name or ''
            ext = nombre_archivo.rsplit('.', 1)[-1].lower() if '.' in nombre_archivo else ''

            if ext not in ADJUNTO_EXTENSIONES_PERMITIDAS:
                messages.error(request, 'Tipo de archivo no permitido. Usa imágenes (jpg, png, gif, webp) o PDF.')
                return render(request, 'inicio/crear_comunicado.html', contexto_error)

            if adjunto_file.size > ADJUNTO_MAX_SIZE:
                messages.error(request, 'El archivo adjunto excede el tamaño máximo permitido (10 MB).')
                return render(request, 'inicio/crear_comunicado.html', contexto_error)

        adjunto_resultado = None
        if adjunto_file:
            try:
                adjunto_resultado = cloudinary.uploader.upload(
                    adjunto_file, folder='fray/comunicados/', resource_type='auto',
                )
            except Exception:
                logger.exception('Error subiendo adjunto de comunicado')
                messages.warning(request, 'El adjunto no se pudo subir. El comunicado se publicará sin archivo adjunto.')

        creados = []
        if destinatario == 'GRUPO':
            grupos_validos = grupos_base.filter(pk__in=grupo_ids)
            if asignatura_id:
                grupos_validos = grupos_validos.filter(asignaturas=asignatura_id)
            grupos_validos = grupos_validos.distinct()

            if not grupos_validos.exists():
                messages.error(
                    request,
                    'Ninguno de los grupos seleccionados es válido (verifica que el ciclo escolar esté activo).'
                )
                return render(request, 'inicio/crear_comunicado.html', contexto_error)

            for grupo in grupos_validos:
                c = Comunicado(
                    plantel=plantel, autor=request.user, titulo=titulo, cuerpo=cuerpo,
                    destinatario='GRUPO', publico=publico, grupo=grupo, asignatura=asignatura,
                )
                if adjunto_resultado:
                    c.adjunto = adjunto_resultado['secure_url']
                creados.append(c)
        else:
            c = Comunicado(
                plantel=plantel, autor=request.user, titulo=titulo, cuerpo=cuerpo,
                destinatario=destinatario, publico=publico, grupo=None, asignatura=asignatura,
            )
            if adjunto_resultado:
                c.adjunto = adjunto_resultado['secure_url']
            creados.append(c)

        if creados:
            Comunicado.objects.bulk_create(creados)
            n = len(creados)
            messages.success(request, f'✅ Comunicado "{titulo}" publicado ({n} grupo{"s" if n != 1 else ""}).')
            return redirect('lista_comunicados')

    return render(request, 'inicio/crear_comunicado.html', {
        'grupos': grupos,
        'asignaturas': asignaturas,
        'es_docente': es_docente,
        'es_directivo': es_directivo,
    })


@login_required
def eliminar_comunicado(request, pk):
    """
    CORRECCIÓN DE SEGURIDAD: antes, cualquier usuario con rol DOCENTE podía
    eliminar el comunicado de CUALQUIER otro usuario del plantel. Ahora: un
    docente solo puede eliminar los comunicados de los que es autor; solo
    DIRECTOR/COORD/ADMIN pueden eliminar cualquier comunicado del plantel.
    """
    from academic.models import Comunicado

    comunicado = get_object_or_404(Comunicado, pk=pk, plantel=request.user.plantel)

    es_directivo = request.user.rol in ('DIRECTOR', 'COORD', 'ADMIN')
    es_autor = comunicado.autor_id == request.user.id

    if not (es_directivo or es_autor):
        messages.error(request, 'No tienes permiso para eliminar este comunicado.')
        return redirect('lista_comunicados')

    if request.method == 'POST':
        comunicado.activo = False
        comunicado.save()
        messages.success(request, 'Comunicado eliminado.')
    return redirect('lista_comunicados')


@login_required
def ver_adjunto_comunicado(request, pk):
    """
    CORRECCIÓN DE SEGURIDAD (SSRF): se valida que el host esté en una lista
    blanca antes de hacer cualquier petición saliente desde el servidor.
    """
    from academic.models import Comunicado
    import requests as req
    from django.conf import settings
    from django.http import HttpResponse

    comunicado = get_object_or_404(Comunicado, pk=pk, plantel=request.user.plantel)

    valor = str(comunicado.adjunto) if comunicado.adjunto else None
    if not valor:
        return redirect('lista_comunicados')

    content_types = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'webp': 'image/webp', 'pdf': 'application/pdf',
    }

    if valor.startswith('http://') or valor.startswith('https://'):
        host = urlparse(valor).hostname or ''
        if host not in ADJUNTO_HOSTS_PERMITIDOS:
            logger.warning('Intento de acceder a adjunto con host no permitido: %s (comunicado %s)', host, pk)
            return HttpResponse('Adjunto no disponible.', status=400)
        candidatos = [valor]
    else:
        cloud = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
        nombre = valor.rsplit('/', 1)[-1]
        tiene_ext = '.' in nombre

        valores_a_probar = [valor]
        if not tiene_ext:
            valores_a_probar += [f'{valor}.jpg', f'{valor}.png', f'{valor}.pdf']

        candidatos = []
        for v in valores_a_probar:
            candidatos.append(f'https://res.cloudinary.com/{cloud}/raw/upload/{v}')
            candidatos.append(f'https://res.cloudinary.com/{cloud}/image/upload/{v}')

    r = None
    url_exitosa = None
    for url in candidatos:
        try:
            r = req.get(url, timeout=5)
        except req.RequestException:
            continue
        if r.status_code == 200:
            url_exitosa = url
            break

    if not url_exitosa:
        return HttpResponse('No se pudo obtener el archivo adjunto.', status=502)

    ext = url_exitosa.rsplit('.', 1)[-1].lower() if '.' in url_exitosa.rsplit('/', 1)[-1] else ''
    content_type = content_types.get(ext, 'application/octet-stream')

    response = HttpResponse(r.content, content_type=content_type)
    response['Content-Disposition'] = 'inline; filename="comunicado.' + (ext or 'bin') + '"'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def en_construccion(request):
    if request.user.is_authenticated:
        theme = get_campus_theme(request.user)
    else:
        theme = {}
    return render(request, 'inicio/en_construccion.html', theme)


@require_http_methods(["GET"])
def api_periodo_activo(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no autenticado'
            }, status=401)

        periodo = None
        plantel = _plantel_del_usuario(request)

        if plantel:
            periodo = Periodo.objects.filter(
                plantel=plantel,
                activo=True
            ).first()
        elif request.user.is_superuser:
            periodo = Periodo.objects.filter(activo=True).first()

        if not periodo:
            return JsonResponse({
                'success': False,
                'error': 'No hay período activo configurado'
            }, status=404)

        try:
            if hasattr(periodo, 'get_display_name') and callable(periodo.get_display_name):
                display_name = periodo.get_display_name()
            else:
                display_name = f"{periodo.fecha_inicio.year} {periodo.fecha_inicio.strftime('%B')}–{periodo.fecha_fin.strftime('%B')} ({periodo.tipo})"
        except Exception:
            logger.exception('Error generando display_name para período %s', periodo.id)
            display_name = f"Período {periodo.id} ({periodo.tipo})"

        return JsonResponse({
            'success': True,
            'periodo': {
                'id': periodo.id,
                'display_name': display_name,
                'tipo': periodo.tipo
            }
        })

    except Exception:
        logger.exception('Error inesperado en api_periodo_activo')
        return JsonResponse({
            'success': False,
            'error': 'Error del servidor. Intenta de nuevo más tarde.'
        }, status=500)


@login_required
def lista_graduados(request):
    if request.user.rol not in ('DIRECTOR', 'COORD', 'ADMIN'):
        messages.error(request, 'No tienes permiso para ver esta sección.')
        return redirect('dashboard')

    plantel = _plantel_del_usuario(request)
    if not plantel:
        messages.error(request, 'Tu cuenta no tiene un plantel asignado.')
        return redirect('dashboard')

    grupos_graduados = Grupo.objects.filter(
        plantel=plantel, grado=6, periodo__activo=False
    ).select_related('periodo', 'carrera').prefetch_related('alumnos').order_by(
        '-periodo__fecha_fin', 'carrera__nombre', 'nombre'
    )

    from itertools import groupby
    periodos_con_grupos = []
    for periodo, grupos in groupby(grupos_graduados, key=lambda g: g.periodo):
        grupos_lista = list(grupos)
        periodos_con_grupos.append({
            'periodo': periodo,
            'grupos': grupos_lista,
            'total_alumnos': sum(g.alumnos.count() for g in grupos_lista),
        })

    return render(request, 'inicio/graduados.html', {
        'periodos_con_grupos': periodos_con_grupos,
    })


# ─────────────────────────────────────────────────────────────────────────────
# BÚSQUEDA GLOBAL AJAX (10 SUGERENCIAS)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def buscar_global(request):
    """
    Buscador global del sistema con 10 sugerencias máximas.

    Todas las URLs de resultado se construyen con reverse() usando los
    nombres reales definidos en cada urls.py de app (academic, users) —
    nunca con f-strings hardcodeados — para que un cambio de prefijo o
    de app no rompa el buscador silenciosamente.
    """
    query = request.GET.get('q', '').strip()

    if len(query) > BUSQUEDA_MAX_LEN:
        query = query[:BUSQUEDA_MAX_LEN]

    if len(query) < 1:
        return JsonResponse({
            'ok': True,
            'query': query,
            'total': 0,
            'resultados': []
        })

    plantel = _plantel_del_usuario(request)
    if not plantel:
        return JsonResponse({
            'ok': False,
            'error': 'Tu cuenta no tiene un plantel asignado.'
        }, status=403)

    resultados = []
    LIMITE_TOTAL = 10

    # ─── ALUMNOS ─────────────────────────────────────────────────────
    alumnos = (
        User.objects
        .filter(plantel=plantel, rol='ALUMNO')
        .filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
        .select_related('plantel', 'alumno_grupo', 'alumno_grupo__carrera')
        .order_by('last_name', 'first_name')[:LIMITE_TOTAL]
    )

    for alumno in alumnos:
        if len(resultados) >= LIMITE_TOTAL:
            break

        nombre = alumno.get_full_name().strip() or alumno.username
        grupo = alumno.alumno_grupo
        grupo_str = f"{grupo}" if grupo else "Sin grupo"

        resultados.append({
            'tipo': 'alumno',
            'id': alumno.pk,
            'titulo': nombre,
            'subtitulo': grupo_str,
            'icono': '👨‍🎓',
            'url': reverse('detalle_alumno', args=[alumno.pk]),
        })

    # ─── DOCENTES ────────────────────────────────────────────────────
    if len(resultados) < LIMITE_TOTAL:
        docentes = (
            User.objects
            .filter(plantel=plantel, rol='DOCENTE')
            .filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query) |
                Q(email__icontains=query)
            )
            .order_by('last_name', 'first_name')[:LIMITE_TOTAL]
        )

        for docente in docentes:
            if len(resultados) >= LIMITE_TOTAL:
                break

            nombre = docente.get_full_name().strip() or docente.username
            subtitulo = docente.email if docente.email else "Docente"

            resultados.append({
                'tipo': 'docente',
                'id': docente.pk,
                'titulo': nombre,
                'subtitulo': subtitulo,
                'icono': '👨‍🏫',
                'url': reverse('detalle_docente', args=[docente.pk]),
            })

    # ─── COORDINADORES ───────────────────────────────────────────────
    if len(resultados) < LIMITE_TOTAL:
        coordinadores = (
            User.objects
            .filter(plantel=plantel, rol='COORD')
            .filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query) |
                Q(email__icontains=query)
            )
            .order_by('last_name', 'first_name')[:LIMITE_TOTAL]
        )

        for coordinador in coordinadores:
            if len(resultados) >= LIMITE_TOTAL:
                break

            nombre = coordinador.get_full_name().strip() or coordinador.username
            subtitulo = coordinador.email if coordinador.email else "Coordinador"

            resultados.append({
                'tipo': 'coordinador',
                'id': coordinador.pk,
                'titulo': nombre,
                'subtitulo': subtitulo,
                'icono': '👔',
                'url': reverse('detalle_coordinador', args=[coordinador.pk]),
            })

    # ─── GRUPOS ──────────────────────────────────────────────────────
    if len(resultados) < LIMITE_TOTAL:
        grupos = (
            Grupo.objects
            .filter(plantel=plantel)
            .filter(
                Q(nombre__icontains=query) |
                Q(carrera__nombre__icontains=query) |
                Q(especialidad__icontains=query)
            )
            .select_related('carrera', 'periodo')
            .order_by('grado', 'nombre')[:LIMITE_TOTAL]
        )

        for grupo in grupos:
            if len(resultados) >= LIMITE_TOTAL:
                break

            carrera = grupo.carrera.nombre if grupo.carrera else 'General'
            subtitulo = f"{carrera} · Grado {grupo.grado}"

            resultados.append({
                'tipo': 'grupo',
                'id': grupo.pk,
                'titulo': str(grupo),
                'subtitulo': subtitulo,
                'icono': '👥',
                'url': reverse('detalle_grupo', args=[grupo.pk]),
            })

    # ─── ASIGNATURAS ─────────────────────────────────────────────────
    # No existe una vista de detalle individual por asignatura en tu
    # urls.py actual — 'asignaturas/' solo lista todas. Se enlaza ahí
    # con reverse('lista_asignaturas'); si en el futuro agregas una vista
    # de detalle por pk, cambia esta línea a reverse('detalle_asignatura', args=[asignatura.pk]).
    if len(resultados) < LIMITE_TOTAL:
        asignaturas = (
            Asignatura.objects
            .filter(carrera__plantel=plantel)
            .filter(
                Q(nombre__icontains=query) |
                Q(clave__icontains=query) |
                Q(carrera__nombre__icontains=query)
            )
            .select_related('carrera')
            .order_by('nombre')[:LIMITE_TOTAL]
        )

        for asignatura in asignaturas:
            if len(resultados) >= LIMITE_TOTAL:
                break

            carrera = asignatura.carrera.nombre if asignatura.carrera else 'General'
            subtitulo = f"Clave: {asignatura.clave}" if asignatura.clave else carrera

            resultados.append({
                'tipo': 'asignatura',
                'id': asignatura.pk,
                'titulo': asignatura.nombre,
                'subtitulo': subtitulo,
                'icono': '📚',
                'url': reverse('lista_asignaturas'),
            })

    # ─── ORDENAR POR PRIORIDAD ───────────────────────────────────────
    prioridad = {
        'alumno': 1,
        'docente': 2,
        'coordinador': 3,
        'grupo': 4,
        'asignatura': 5,
    }

    resultados.sort(key=lambda r: prioridad.get(r['tipo'], 99))

    return JsonResponse({
        'ok': True,
        'query': query,
        'total': len(resultados),
        'resultados': resultados,
    })