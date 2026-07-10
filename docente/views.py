# Imports estándar
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q, Avg
from django.views.decorators.http import require_POST
# ReportLab — para PDFs
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Modelos
from users.models import User, DocenteGrupo
from academic.models import (
    Grupo, Asignatura, Asistencia, Calificacion,
    Tarea, EntregaTarea, ComentarioTarea,
    Actividad, EntregaActividad,
    MaterialApoyo, CarpetaMaterial, ComentarioMaterial,
)

# Cloudinary
import cloudinary
import requests as req
from academic.models import (
    PlanClase, TemaClase, Grupo, Asignatura,
    Calificacion, Asistencia
)
import datetime

# ─────────────────────────────────────────────────────────────────────────────
# DECORADOR
# ─────────────────────────────────────────────────────────────────────────────

def docente_required(view_func):
    """Solo docentes pueden acceder."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.rol != 'DOCENTE':
            messages.error(request, 'No tienes permiso para acceder a esa sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: verificar que el grupo pertenece al plantel del docente
# ─────────────────────────────────────────────────────────────────────────────

def _get_grupo_seguro(grupo_id, docente):
    """
    Devuelve el grupo solo si:
      1. Existe
      2. Pertenece al plantel del docente (o al plantel donde está activo si es multi-plantel)
      3. El docente tiene una asignación activa en él
    Lanza 404 en cualquier otro caso.
    """
    from academic.models import Grupo
    return get_object_or_404(
        Grupo,
        pk=grupo_id,
        plantel=docente.plantel,                      # Fix: filtro de plantel
        docentes_asignados__docente=docente,
        docentes_asignados__activo=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD DOCENTE  (antes vivía en inicio/views.py)
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def dashboard_docente(request):
    from academic.models import Grupo, Asistencia
    from users.views import get_campus_theme

    theme   = get_campus_theme(request.user)
    plantel = request.user.plantel
    hoy     = timezone.now().date()

    # Solo grupos del plantel actual del docente
    grupos = (
        Grupo.objects
        .filter(
            plantel=plantel,                          # Fix: filtro plantel
            docentes_asignados__docente=request.user,
            docentes_asignados__activo=True,
        )
        .distinct()
        .prefetch_related('alumnos', 'asignaturas')
    )

    total_alumnos = (
        __import__('users').models.User.objects
        .filter(rol='ALUMNO', alumno_grupo__in=grupos)
        .distinct().count()
    )

    alumnos_riesgo = (
        __import__('users').models.User.objects
        .filter(rol='ALUMNO', alumno_grupo__in=grupos, notas__nota__lt=6.0)
        .distinct()[:5]
    )

    registros_hoy = Asistencia.objects.filter(grupo__in=grupos, fecha=hoy).count()
    presentes_hoy = Asistencia.objects.filter(grupo__in=grupos, fecha=hoy, estado='P').count()
    asistencia_hoy = (
        f"{int((presentes_hoy / registros_hoy) * 100)}%"
        if registros_hoy > 0 else "Sin registro"
    )

    return render(request, 'inicio/dashboard_docente.html', {
        'grupos':         grupos,
        'total_alumnos':  total_alumnos,
        'alumnos_riesgo': alumnos_riesgo,
        'asistencia_hoy': asistencia_hoy,
        'hoy':            hoy,
        **theme,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MI ESPACIO
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def mis_grupos(request):
    from academic.models import Grupo
    grupos = (
        Grupo.objects
        .filter(
            plantel=request.user.plantel,
            docentes=request.user,
            asignaturas__docentes=request.user,   # ← solo grupos donde también imparte alguna materia
        )
        .distinct()
        .prefetch_related('alumnos', 'asignaturas')
    )
    return render(request, 'docente/mis_grupos.html', {'grupos': grupos})


@docente_required
def mi_horario(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            grupo__plantel=request.user.plantel,      # Fix: filtro plantel
        )
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/mi_horario.html', {'asignaciones': asignaciones})


# ─────────────────────────────────────────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def lista_asistencia(request):
    from academic.models import Asistencia, Grupo, Asignatura
    from datetime import date

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix: filtro plantel
        )
        .select_related('grupo', 'asignatura', 'grupo__carrera')
        .order_by('grupo__nombre', 'asignatura__nombre')
    )

    grupo_id      = request.POST.get('grupo_id')      or request.GET.get('grupo_id')
    asignatura_id = request.POST.get('asignatura_id') or request.GET.get('asignatura_id')
    fecha_str     = request.POST.get('fecha')         or request.GET.get('fecha')

    try:
        fecha = date.fromisoformat(fecha_str) if fecha_str else date.today()
    except ValueError:
        fecha = date.today()

    grupo      = None
    asignatura = None
    filas      = []
    ya_guardado = False

    if grupo_id and asignatura_id:
        asignacion = asignaciones.filter(
            grupo_id=grupo_id,
            asignatura_id=asignatura_id,
        ).first()

        if not asignacion:
            messages.error(request, 'No tienes permiso para ese grupo/asignatura.')
            return redirect('docente_lista_asistencia')

        grupo      = asignacion.grupo
        asignatura = asignacion.asignatura

        alumnos = (
            grupo.alumnos
            .filter(estatus='ACTIVO', rol='ALUMNO')
            .order_by('last_name', 'first_name')
        )

        registros_hoy = {
            r.alumno_id: r.estado
            for r in Asistencia.objects.filter(
                grupo=grupo, asignatura=asignatura, fecha=fecha,
            )
        }
        ya_guardado = bool(registros_hoy)

        resumen_qs = Asistencia.objects.filter(
            grupo=grupo, asignatura=asignatura,
            fecha__month=fecha.month, fecha__year=fecha.year,
        ).values('alumno_id').annotate(
            presentes=Count('id', filter=Q(estado='P')),
            ausentes =Count('id', filter=Q(estado='A')),
            retardos =Count('id', filter=Q(estado='R')),
        )
        resumen = {r['alumno_id']: r for r in resumen_qs}

        for alumno in alumnos:
            estado_actual = registros_hoy.get(alumno.pk, 'P')
            res = resumen.get(alumno.pk, {'presentes': 0, 'ausentes': 0, 'retardos': 0})
            filas.append({
                'alumno':    alumno,
                'estado':    estado_actual,
                'es_P':      estado_actual == 'P',
                'es_A':      estado_actual == 'A',
                'es_R':      estado_actual == 'R',
                'presentes': res['presentes'],
                'ausentes':  res['ausentes'],
                'retardos':  res['retardos'],
            })

        if request.method == 'POST' and 'guardar' in request.POST:
            for fila in filas:
                alumno = fila['alumno']
                estado = request.POST.get(f'estado_{alumno.pk}', 'A')
                if estado not in ('P', 'A', 'R'):
                    estado = 'A'

                # Si asignatura es None, usar filter+update o create explícito
                if asignatura:
                    Asistencia.objects.update_or_create(
                        alumno=alumno,
                        grupo=grupo,
                        asignatura=asignatura,
                        fecha=fecha,
                        defaults={'estado': estado},
                    )
                else:
                    # Sin asignatura, buscar manualmente para no duplicar
                    obj, created = Asistencia.objects.get_or_create(
                        alumno=alumno,
                        grupo=grupo,
                        asignatura=None,
                        fecha=fecha,
                        defaults={'estado': estado},
                    )
                    if not created:
                        obj.estado = estado
                        obj.save()

            messages.success(request, f'✅ Asistencia del {fecha.strftime("%d/%m/%Y")} guardada.')
            return redirect(
                f"{request.path}?grupo_id={grupo_id}&asignatura_id={asignatura_id}&fecha={fecha}"
            )
    return render(request, 'docente/asistencia.html', {
        'asignaciones': asignaciones,
        'grupo':        grupo,
        'asignatura':   asignatura,
        'filas':        filas,
        'fecha':        fecha,
        'ya_guardado':  ya_guardado,
        'hoy':          timezone.now().date(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# TAREAS
# ─────────────────────────────────────────────────────────────────────────────
@docente_required
@require_POST
def publicar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)
    tarea.publicada = True
    tarea.save(update_fields=['publicada'])
    return redirect('docente_tareas')

@docente_required
@require_POST
def publicar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)
    actividad.publicada = True
    actividad.publicada_en = timezone.now()
    actividad.save(update_fields=['publicada', 'publicada_en'])
    messages.success(request, f'✅ Actividad "{actividad.titulo}" publicada.')
    return redirect('docente_actividades')
 

@docente_required
def tareas(request):
    from academic.models import Tarea

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    grupo_id      = request.GET.get('grupo_id', '')
    asignatura_id = request.GET.get('asignatura_id', '')
    ahora         = timezone.now()

    qs = (
        Tarea.objects
        .filter(docente=request.user, activa=True)
        .select_related('grupo', 'asignatura')
        .annotate(
            total_entregas=Count('entregas'),
            entregas_calificadas=Count('entregas', filter=Q(entregas__estado='CALIFICADA')),
        )
    )

    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        qs = qs.filter(asignatura_id=asignatura_id)

    activas    = qs.filter(publicada=True,  fecha_entrega__gte=ahora)
    vencidas   = qs.filter(publicada=True,  fecha_entrega__lt=ahora)
    borradores = qs.filter(publicada=False)

    return render(request, 'docente/tareas.html', {
        'asignaciones':  asignaciones,
        'activas':       activas,
        'vencidas':      vencidas,
        'borradores':    borradores,
        'grupo_id':      grupo_id,
        'asignatura_id': asignatura_id,
    })


@docente_required
def crear_tarea(request):
    from academic.models import Tarea

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    if request.method == 'POST':
        grupo_id      = request.POST.get('grupo_id')
        asignatura_id = request.POST.get('asignatura_id')
        titulo        = request.POST.get('titulo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        fecha_entrega = request.POST.get('fecha_entrega')
        archivo       = request.FILES.get('archivo')

        if not all([grupo_id, asignatura_id, titulo, fecha_entrega]):
            messages.error(request, 'Completa todos los campos obligatorios.')
        else:
            asignacion = asignaciones.filter(
                grupo_id=grupo_id, asignatura_id=asignatura_id
            ).first()
            if not asignacion:
                messages.error(request, 'No tienes permiso para ese grupo/asignatura.')
            else:
                tarea = Tarea.objects.create(
                    docente=request.user,
                    grupo=asignacion.grupo,
                    asignatura=asignacion.asignatura,
                    titulo=titulo,
                    descripcion=descripcion,
                    fecha_entrega=fecha_entrega,
                    archivo=archivo,
                    publicada=request.POST.get('publicada') == '1',
                )
                messages.success(request, f'✅ Tarea "{titulo}" creada correctamente.')
                return redirect('detalle_tarea', pk=tarea.pk)

    return render(request, 'docente/crear_tarea.html', {'asignaciones': asignaciones})


def fix_pdf_url(url):
    url = url.replace('http://', 'https://').replace('/image/upload/', '/raw/upload/')
    if not url.endswith('.pdf'):
        url += '.pdf'
    return url


def detalle_tarea(request, pk):
    from academic.models import Tarea, EntregaTarea, ComentarioTarea

    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)

    alumnos  = tarea.grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO')
    entregas = {e.alumno_id: e for e in tarea.entregas.select_related('alumno').all()}

    filas = []
    for alumno in alumnos:
        entrega = entregas.get(alumno.pk)
        if entrega and entrega.archivo:
            entrega.archivo_url = fix_pdf_url(entrega.archivo.url)
        filas.append({
            'alumno':  alumno,
            'entrega': entrega,
            'estado':  entrega.estado if entrega else 'PENDIENTE',
        })

    if request.method == 'POST' and 'calificar' in request.POST:
        entrega_id   = request.POST.get('entrega_id')
        calificacion = request.POST.get('calificacion')
        feedback     = request.POST.get('feedback', '').strip()
        try:
            entrega = EntregaTarea.objects.get(pk=entrega_id, tarea=tarea)
            entrega.calificacion  = calificacion
            entrega.feedback      = feedback
            entrega.estado        = 'CALIFICADA'
            entrega.calificada_en = timezone.now()
            entrega.save()
            messages.success(request, f'Entrega de {entrega.alumno.get_full_name()} calificada.')
        except EntregaTarea.DoesNotExist:
            messages.error(request, 'Entrega no encontrada.')
        return redirect('detalle_tarea', pk=pk)

    if request.method == 'POST' and 'toggle_publicar' in request.POST:
        tarea.publicada = not tarea.publicada
        tarea.save()
        messages.success(request, f'Tarea {"publicada" if tarea.publicada else "guardada como borrador"}.')
        return redirect('detalle_tarea', pk=pk)

    if request.method == 'POST' and 'comentar' in request.POST:
        texto = request.POST.get('texto', '').strip()
        if texto:
            ComentarioTarea.objects.create(tarea=tarea, autor=request.user, texto=texto)
        return redirect('detalle_tarea', pk=pk)

    # ── Editar comentario propio ──
    if request.method == 'POST' and 'editar_comentario' in request.POST:
        comentario_id = request.POST.get('comentario_id')
        texto_nuevo    = request.POST.get('texto_editado', '').strip()
        try:
            comentario = ComentarioTarea.objects.get(pk=comentario_id, tarea=tarea, autor=request.user)
            if texto_nuevo:
                comentario.texto = texto_nuevo
                comentario.save(update_fields=['texto'])
                messages.success(request, 'Comentario actualizado.')
            else:
                messages.error(request, 'El comentario no puede quedar vacío.')
        except ComentarioTarea.DoesNotExist:
            messages.error(request, 'No puedes editar este comentario.')
        return redirect('detalle_tarea', pk=pk)

    # ── Eliminar comentario propio ──
    if request.method == 'POST' and 'eliminar_comentario' in request.POST:
        comentario_id = request.POST.get('comentario_id')
        try:
            comentario = ComentarioTarea.objects.get(pk=comentario_id, tarea=tarea, autor=request.user)
            comentario.delete()
            messages.success(request, 'Comentario eliminado.')
        except ComentarioTarea.DoesNotExist:
            messages.error(request, 'No puedes eliminar este comentario.')
        return redirect('detalle_tarea', pk=pk)

    comentarios       = tarea.comentarios.select_related('autor').all()
    total_alumnos     = alumnos.count()
    total_entregaron  = len([f for f in filas if f['entrega']])
    total_calificadas = len([f for f in filas if f['estado'] == 'CALIFICADA'])
    total_pendientes  = total_alumnos - total_entregaron
    tarea_archivo_url = fix_pdf_url(tarea.archivo.url) if tarea.archivo else None

    return render(request, 'docente/detalle_tarea.html', {
        'tarea':             tarea,
        'tarea_archivo_url': tarea_archivo_url,
        'filas':             filas,
        'comentarios':       comentarios,
        'total_alumnos':     total_alumnos,
        'total_entregaron':  total_entregaron,
        'total_calificadas': total_calificadas,
        'total_pendientes':  total_pendientes,
    })


@docente_required
def ver_pdf(request, pk, tipo):
    from academic.models import Tarea, EntregaTarea, EntregaActividad

    if tipo == 'tarea':
        obj = get_object_or_404(Tarea, pk=pk, docente=request.user)
    elif tipo == 'entrega':
        obj = get_object_or_404(EntregaTarea, pk=pk, tarea__docente=request.user)
    elif tipo == 'actividad':
        obj = get_object_or_404(EntregaActividad, pk=pk, actividad__docente=request.user)
    else:
        return redirect('docente_tareas')

    valor = str(obj.archivo) if obj.archivo else None
    if not valor:
        return redirect('docente_tareas')

    from django.conf import settings
    from django.http import HttpResponse

    # Si ya es una URL completa (caso de EntregaTarea/EntregaActividad desde Ionic),
    # se usa tal cual. Si es solo un public_id, se construye la URL.
    if valor.startswith('http://') or valor.startswith('https://'):
        url = valor
    else:
        cloud = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
        if not valor.endswith('.pdf'):
            valor += '.pdf'
        url = f'https://res.cloudinary.com/{cloud}/raw/upload/{valor}'

    r = req.get(url)
    if r.status_code != 200:
        return HttpResponse(
            f'No se pudo obtener el archivo de Cloudinary (status {r.status_code}).',
            status=502
        )

    response = HttpResponse(r.content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="documento.pdf"'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@docente_required
def editar_tarea(request, pk):
    from academic.models import Tarea

    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    if request.method == 'POST':
        titulo        = request.POST.get('titulo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        fecha_entrega = request.POST.get('fecha_entrega')
        archivo       = request.FILES.get('archivo')
        publicada     = request.POST.get('publicada') == '1'

        if not all([titulo, fecha_entrega]):
            messages.error(request, 'Título y fecha son obligatorios.')
        else:
            tarea.titulo        = titulo
            tarea.descripcion   = descripcion
            tarea.fecha_entrega = fecha_entrega
            tarea.publicada     = publicada
            if archivo:
                tarea.archivo = archivo
            tarea.save()
            messages.success(request, f'✅ Tarea "{titulo}" actualizada.')
            return redirect('detalle_tarea', pk=pk)

    return render(request, 'docente/editar_tarea.html', {
        'tarea': tarea, 'asignaciones': asignaciones,
    })


@docente_required
def eliminar_tarea(request, pk):
    from academic.models import Tarea
    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada.')
    return redirect('docente_tareas')


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVIDADES
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def actividades(request):
    from academic.models import Actividad

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    grupo_id      = request.GET.get('grupo_id')
    asignatura_id = request.GET.get('asignatura_id')

    qs = (
        Actividad.objects
        .filter(docente=request.user)
        .select_related('grupo', 'asignatura')
        .annotate(total_entregas=Count('entregas'))
    )
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        qs = qs.filter(asignatura_id=asignatura_id)

    ahora = timezone.now()
    return render(request, 'docente/actividades.html', {
        'asignaciones':  asignaciones,
        'activas':       qs.filter(publicada=True,  fecha_entrega__gte=ahora),
        'vencidas':      qs.filter(publicada=True,  fecha_entrega__lt=ahora),
        'borradores':    qs.filter(publicada=False),
        'grupo_id':      grupo_id,
        'asignatura_id': asignatura_id,
    })


@docente_required
def crear_actividad(request):
    from academic.models import Actividad, PreguntaActividad, OpcionRespuesta

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    if request.method == 'POST':
        grupo_id        = request.POST.get('grupo_id')
        asignatura_id   = request.POST.get('asignatura_id')
        titulo          = request.POST.get('titulo', '').strip()
        instrucciones   = request.POST.get('instrucciones', '').strip()
        tipo            = request.POST.get('tipo')
        fecha_entrega   = request.POST.get('fecha_entrega')
        url_interactiva = request.POST.get('url_interactiva', '').strip()
        archivo         = request.FILES.get('archivo')
        cal_auto        = tipo == 'MULTIPLE'

        if not all([grupo_id, asignatura_id, titulo, fecha_entrega, tipo]):
            messages.error(request, 'Completa todos los campos obligatorios.')
        else:
            asignacion = asignaciones.filter(
                grupo_id=grupo_id, asignatura_id=asignatura_id
            ).first()
            if not asignacion:
                messages.error(request, 'No tienes permiso para ese grupo/asignatura.')
            else:
                actividad = Actividad.objects.create(
                    docente=request.user,
                    grupo=asignacion.grupo,
                    asignatura=asignacion.asignatura,
                    titulo=titulo,
                    instrucciones=instrucciones,
                    tipo=tipo,
                    fecha_entrega=fecha_entrega,
                    url_interactiva=url_interactiva if tipo == 'INTERACTIVA' else '',
                    archivo=archivo,
                    calificacion_automatica=cal_auto,
                    publicada=request.POST.get('publicada') == '1',
                )

                if tipo in ('MULTIPLE', 'ABIERTA'):
                    textos   = request.POST.getlist('pregunta_texto')
                    puntos_l = request.POST.getlist('pregunta_puntos')
                    for i, texto in enumerate(textos):
                        if not texto.strip():
                            continue
                        pregunta = PreguntaActividad.objects.create(
                            actividad=actividad,
                            texto=texto.strip(),
                            orden=i,
                            puntos=puntos_l[i] if i < len(puntos_l) else 1,
                        )
                        if tipo == 'MULTIPLE':
                            opciones     = request.POST.getlist(f'opcion_texto_{i}')
                            correcta_idx = request.POST.get(f'opcion_correcta_{i}', '0')
                            for j, op_texto in enumerate(opciones):
                                if op_texto.strip():
                                    OpcionRespuesta.objects.create(
                                        pregunta=pregunta,
                                        texto=op_texto.strip(),
                                        es_correcta=(str(j) == correcta_idx),
                                    )

                messages.success(request, f'✅ Actividad "{titulo}" creada.')
                return redirect('detalle_actividad', pk=actividad.pk)

    return render(request, 'docente/crear_actividad.html', {'asignaciones': asignaciones})


@docente_required
def detalle_actividad(request, pk):
    from academic.models import Actividad, EntregaActividad

    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)
    alumnos   = actividad.grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO')
    entregas  = {e.alumno_id: e for e in actividad.entregas.select_related('alumno').all()}

    filas = []
    for alumno in alumnos:
        entrega = entregas.get(alumno.pk)
        if entrega and entrega.archivo:
            entrega.archivo_url = fix_pdf_url(entrega.archivo.url)
        filas.append({
            'alumno':  alumno,
            'entrega': entrega,
            'estado':  'CALIFICADA' if entrega and entrega.calificacion else ('ENTREGADA' if entrega else 'PENDIENTE'),
        })

    if request.method == 'POST' and 'calificar' in request.POST:
        entrega_id   = request.POST.get('entrega_id')
        calificacion = request.POST.get('calificacion')
        feedback     = request.POST.get('feedback', '').strip()
        try:
            entrega = EntregaActividad.objects.get(pk=entrega_id, actividad=actividad)
            entrega.calificacion = calificacion
            entrega.feedback     = feedback
            entrega.save()
            messages.success(request, 'Entrega calificada.')
        except EntregaActividad.DoesNotExist:
            messages.error(request, 'Entrega no encontrada.')
        return redirect('detalle_actividad', pk=pk)

    if request.method == 'POST' and 'toggle_publicar' in request.POST:
        actividad.publicada    = not actividad.publicada
        actividad.publicada_en = timezone.now() if actividad.publicada else None
        actividad.save()
        messages.success(request, f'Actividad {"publicada" if actividad.publicada else "despublicada"}.')
        return redirect('detalle_actividad', pk=pk)

    return render(request, 'docente/detalle_actividad.html', {
        'actividad':         actividad,
        'filas':             filas,
        'preguntas':         actividad.preguntas.prefetch_related('opciones').all(),
        'total_alumnos':     alumnos.count(),
        'total_entregaron':  len([f for f in filas if f['entrega']]),
        'total_calificadas': len([f for f in filas if f['estado'] == 'CALIFICADA']),
        'total_pendientes':  alumnos.count() - len([f for f in filas if f['entrega']]),
    })


@docente_required
def editar_actividad(request, pk):
    from academic.models import Actividad, PreguntaActividad, OpcionRespuesta

    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    if request.method == 'POST':
        titulo          = request.POST.get('titulo', '').strip()
        instrucciones   = request.POST.get('instrucciones', '').strip()
        fecha_entrega   = request.POST.get('fecha_entrega')
        url_interactiva = request.POST.get('url_interactiva', '').strip()
        archivo         = request.FILES.get('archivo')
        publicada       = request.POST.get('publicada') == '1'

        if not all([titulo, fecha_entrega]):
            messages.error(request, 'Título y fecha son obligatorios.')
        else:
            actividad.titulo          = titulo
            actividad.instrucciones   = instrucciones
            actividad.fecha_entrega   = fecha_entrega
            actividad.url_interactiva = url_interactiva
            actividad.publicada       = publicada
            if archivo:
                actividad.archivo = archivo
            actividad.save()

            if actividad.tipo in ('MULTIPLE', 'ABIERTA'):
                actividad.preguntas.all().delete()
                textos   = request.POST.getlist('pregunta_texto')
                puntos_l = request.POST.getlist('pregunta_puntos')
                for i, texto in enumerate(textos):
                    if not texto.strip():
                        continue
                    pregunta = PreguntaActividad.objects.create(
                        actividad=actividad,
                        texto=texto.strip(),
                        orden=i,
                        puntos=puntos_l[i] if i < len(puntos_l) else 1,
                    )
                    if actividad.tipo == 'MULTIPLE':
                        opciones     = request.POST.getlist(f'opcion_texto_{i}')
                        correcta_idx = request.POST.get(f'opcion_correcta_{i}', '0')
                        for j, op_texto in enumerate(opciones):
                            if op_texto.strip():
                                OpcionRespuesta.objects.create(
                                    pregunta=pregunta,
                                    texto=op_texto.strip(),
                                    es_correcta=(str(j) == correcta_idx),
                                )

            messages.success(request, f'✅ Actividad "{titulo}" actualizada.')
            return redirect('detalle_actividad', pk=pk)

    preguntas = actividad.preguntas.prefetch_related('opciones').order_by('orden')
    return render(request, 'docente/editar_actividad.html', {
        'actividad': actividad, 'asignaciones': asignaciones, 'preguntas': preguntas,
    })


@docente_required
def eliminar_actividad(request, pk):
    from academic.models import Actividad
    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)
    if request.method == 'POST':
        actividad.delete()
        messages.success(request, 'Actividad eliminada.')
    return redirect('docente_actividades')


# ─────────────────────────────────────────────────────────────────────────────
# CALIFICACIONES / BOLETA / CONCENTRADO
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def calificar_tareas(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, grupo__plantel=request.user.plantel)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/calificar_tareas.html', {'asignaciones': asignaciones})


# Reemplaza la función calificar_actividades en docente/views.py

@docente_required
def calificar_actividades(request):
    from academic.models import Actividad, EntregaActividad, Calificacion
    from users.models import User

    grupos = Grupo.objects.filter(
        plantel=request.user.plantel, docentes=request.user
    ).prefetch_related('asignaturas')

    grupo_id     = request.GET.get('grupo_id') or request.POST.get('grupo_id')
    actividad_id = request.GET.get('actividad_id') or request.POST.get('actividad_id')

    grupo_sel = None
    act_sel   = None
    alumnos   = []

    # Actividades del docente (filtrando por grupo si se eligió)
    actividades_qs = Actividad.objects.filter(
        docente=request.user
    ).select_related('grupo').order_by('-fecha_creacion')

    if grupo_id:
        grupo_sel = get_object_or_404(
            Grupo, pk=grupo_id, plantel=request.user.plantel, docentes=request.user
        )
        actividades_qs = actividades_qs.filter(grupo=grupo_sel)

    if actividad_id:
        act_sel = get_object_or_404(
            Actividad, pk=actividad_id, docente=request.user
        )
        if not grupo_sel:
            grupo_sel = act_sel.grupo

        alumnos_qs = User.objects.filter(
            rol='ALUMNO', alumno_grupo=grupo_sel, estatus='ACTIVO'
        ).order_by('last_name', 'first_name')

        # Mapa de entregas existentes
        entregas = {
            e.alumno_id: e
            for e in EntregaActividad.objects.filter(actividad=act_sel)
        }

        # Calificaciones ya guardadas
        calif_existentes = {
            c.alumno_id: c.nota
            for c in Calificacion.objects.filter(
                alumno__in=alumnos_qs,
                asignatura=act_sel.asignatura if hasattr(act_sel, 'asignatura') else None,
            )
        } if hasattr(act_sel, 'asignatura') and act_sel.asignatura else {}

        alumnos = [
            {
                'alumno':    a,
                'entregado': a.pk in entregas,
                'nota':      calif_existentes.get(a.pk, ''),
            }
            for a in alumnos_qs
        ]

        # Guardar calificaciones
        if request.method == 'POST' and request.POST.get('guardar'):
            guardados = 0
            for fila in alumnos:
                alumno = fila['alumno']
                raw = request.POST.get(f'nota_{alumno.pk}', '').strip()
                if raw == '':
                    continue
                try:
                    nota = round(max(0.0, min(float(act_sel.valor_maximo), float(raw.replace(',', '.')))), 2)
                    # Guardar en EntregaActividad si existe
                    entrega = entregas.get(alumno.pk)
                    if entrega:
                        entrega.calificacion = nota
                        entrega.save(update_fields=['calificacion'])
                    guardados += 1
                except (ValueError, AttributeError):
                    pass

            messages.success(request, f'{guardados} calificaciones guardadas en "{act_sel.titulo}".')
            return redirect(
                f"{request.path}?grupo_id={grupo_sel.pk}&actividad_id={act_sel.pk}"
            )

    return render(request, 'docente/calificar_actividades.html', {
        'grupos':      grupos,
        'actividades': actividades_qs,
        'grupo_sel':   grupo_sel,
        'act_sel':     act_sel,
        'alumnos':     alumnos,
    })


@docente_required
def boleta(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, grupo__plantel=request.user.plantel)
        .select_related('grupo', 'asignatura')
        .values('grupo__pk', 'grupo__nombre', 'grupo__grado', 'asignatura__pk', 'asignatura__nombre')
        .distinct()
        .order_by('grupo__grado', 'grupo__nombre', 'asignatura__nombre')
    )
    return render(request, 'docente/boleta.html', {'asignaciones': asignaciones})

@docente_required
def boleta_grupo(request, grupo_id, asignatura_id):
    from academic.models import Grupo, Asignatura, Calificacion, EntregaTarea, EntregaActividad
    from users.models import DocenteGrupo, User
    from django.db.models import Avg

    grupo = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)

    tiene_acceso = DocenteGrupo.objects.filter(
        docente=request.user, grupo=grupo, asignatura=asignatura, activo=True
    ).exists()
    if not tiene_acceso:
        messages.error(request, 'No tienes acceso a esta materia en este grupo.')
        return redirect('docente_boleta_lista')

    alumnos = User.objects.filter(
        rol='ALUMNO', alumno_grupo=grupo, plantel=request.user.plantel
    ).order_by('last_name', 'first_name')

    if request.method == 'POST':
        for alumno in alumnos:
            valor = request.POST.get(f'cal_{alumno.pk}')
            if valor:
                Calificacion.objects.update_or_create(
                    alumno=alumno, asignatura=asignatura, grupo=grupo, tipo='MANUAL',
                    defaults={'nota': valor, 'docente': request.user}
                )
        messages.success(request, 'Calificaciones guardadas.')
        return redirect('docente_boleta_grupo', grupo_id=grupo.pk, asignatura_id=asignatura.pk)

    filas = []
    for alumno in alumnos:
        prom_tareas = EntregaTarea.objects.filter(
            alumno=alumno, tarea__grupo=grupo, tarea__asignatura=asignatura, calificacion__isnull=False
        ).aggregate(p=Avg('calificacion'))['p']

        prom_activ = EntregaActividad.objects.filter(
            alumno=alumno, actividad__grupo=grupo, actividad__asignatura=asignatura, calificacion__isnull=False
        ).aggregate(p=Avg('calificacion'))['p']

        manual_obj = Calificacion.objects.filter(
            alumno=alumno, asignatura=asignatura, grupo=grupo, tipo='MANUAL'
        ).order_by('-fecha').first()
        manual_val = manual_obj.nota if manual_obj else None

        partes = [v for v in [prom_tareas, prom_activ, manual_val] if v is not None]
        final = round(sum(partes) / len(partes), 2) if partes else None

        filas.append({
            'alumno': alumno,
            'prom_tareas': round(prom_tareas, 2) if prom_tareas else None,
            'prom_activ': round(prom_activ, 2) if prom_activ else None,
            'manual': manual_val,
            'final': final,
        })

    return render(request, 'docente/boleta_grupo.html', {
        'grupo': grupo,
        'asignatura': asignatura,
        'filas': filas,
    })


@docente_required
def concentrado(request):
    from academic.models import Grupo, Calificacion, EntregaTarea, EntregaActividad

    grupo_id = request.GET.get('grupo_id')

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )
    grupos = list({a.grupo for a in asignaciones})

    grupo       = None
    filas       = []
    asignaturas = []

    if grupo_id:
        # Fix crítico: verificar plantel
        grupo = get_object_or_404(
            Grupo,
            pk=grupo_id,
            plantel=request.user.plantel,             # Fix
        )
        if not asignaciones.filter(grupo=grupo).exists():
            messages.error(request, 'No tienes acceso a este grupo.')
            return redirect('docente_concentrado')

        asignaturas = [a.asignatura for a in asignaciones.filter(grupo=grupo)]
        alumnos     = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

        for alumno in alumnos:
            cols = []
            for asig in asignaturas:
                prom_tareas = EntregaTarea.objects.filter(
                    alumno=alumno, tarea__asignatura=asig,
                    tarea__grupo=grupo, calificacion__isnull=False,
                ).aggregate(p=Avg('calificacion'))['p']

                prom_activ = EntregaActividad.objects.filter(
                    alumno=alumno, actividad__asignatura=asig,
                    actividad__grupo=grupo, calificacion__isnull=False,
                ).aggregate(p=Avg('calificacion'))['p']

                cal_manual = Calificacion.objects.filter(
                    alumno=alumno, asignatura=asig, grupo=grupo, tipo='MANUAL',
                ).first()

                valores = [v for v in [
                    prom_tareas, prom_activ,
                    cal_manual.nota if cal_manual else None,
                ] if v is not None]
                cols.append(round(sum(valores) / len(valores), 2) if valores else None)

            valores_fila     = [c for c in cols if c is not None]
            promedio_general = round(sum(valores_fila) / len(valores_fila), 2) if valores_fila else None
            filas.append({'alumno': alumno, 'cols': cols, 'promedio_general': promedio_general})

    return render(request, 'docente/concentrado.html', {
        'grupos': grupos, 'grupo': grupo, 'asignaturas': asignaturas,
        'filas': filas, 'grupo_id': grupo_id,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL DE APOYO
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def material_apoyo(request):
    from academic.models import MaterialApoyo, CarpetaMaterial

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    grupo_id      = request.GET.get('grupo_id', '')
    asignatura_id = request.GET.get('asignatura_id', '')
    tipo_filtro   = request.GET.get('tipo', '')
    carpeta_id    = request.GET.get('carpeta_id', '')
    q             = request.GET.get('q', '').strip()

    qs = (
        MaterialApoyo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura', 'carpeta')
    )
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        qs = qs.filter(asignatura_id=asignatura_id)
    if tipo_filtro:
        qs = qs.filter(tipo=tipo_filtro)
    if carpeta_id:
        qs = qs.filter(carpeta_id=carpeta_id)
    if q:
        qs = qs.filter(titulo__icontains=q)

    carpetas_qs = CarpetaMaterial.objects.filter(docente=request.user)
    if grupo_id:
        carpetas_qs = carpetas_qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        carpetas_qs = carpetas_qs.filter(asignatura_id=asignatura_id)
    carpetas_qs = carpetas_qs.annotate(total=Count('materiales'))

    sin_carpeta = qs.filter(carpeta__isnull=True)
    con_carpeta = {}
    for carpeta in carpetas_qs:
        mats = qs.filter(carpeta=carpeta)
        if mats.exists() or not q:
            con_carpeta[carpeta] = mats

    conteos = {c['tipo']: c['n'] for c in qs.values('tipo').annotate(n=Count('id'))}

    return render(request, 'docente/material.html', {
        'asignaciones':  asignaciones,
        'sin_carpeta':   sin_carpeta,
        'con_carpeta':   con_carpeta,
        'carpetas':      carpetas_qs,
        'grupo_id':      grupo_id,
        'asignatura_id': asignatura_id,
        'tipo_filtro':   tipo_filtro,
        'carpeta_id':    carpeta_id,
        'q':             q,
        'conteos':       conteos,
        'total':         qs.count(),
        'tipos':         MaterialApoyo.TIPOS,
    })


@docente_required
def subir_material(request):
    from academic.models import MaterialApoyo, CarpetaMaterial

    asignaciones = (
        DocenteGrupo.objects
        .filter(
            docente=request.user,
            activo=True,
            asignatura__isnull=False,
            grupo__plantel=request.user.plantel,      # Fix
        )
        .select_related('grupo', 'asignatura')
    )

    if request.method == 'POST':
        grupo_id      = request.POST.get('grupo_id')
        asignatura_id = request.POST.get('asignatura_id')
        titulo        = request.POST.get('titulo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        tipo          = request.POST.get('tipo')
        url_externa   = request.POST.get('url_externa', '').strip()
        archivo       = request.FILES.get('archivo')
        carpeta_id    = request.POST.get('carpeta_id') or None
        nueva_carpeta = request.POST.get('nueva_carpeta', '').strip()

        if not all([grupo_id, asignatura_id, titulo, tipo]):
            messages.error(request, 'Completa todos los campos obligatorios.')
        else:
            asignacion = asignaciones.filter(
                grupo_id=grupo_id, asignatura_id=asignatura_id
            ).first()
            if not asignacion:
                messages.error(request, 'No tienes permiso para ese grupo/asignatura.')
            else:
                if nueva_carpeta:
                    carpeta_obj, _ = CarpetaMaterial.objects.get_or_create(
                        docente=request.user,
                        grupo=asignacion.grupo,
                        asignatura=asignacion.asignatura,
                        nombre=nueva_carpeta,
                    )
                    carpeta_id = carpeta_obj.pk
                elif carpeta_id:
                    carpeta_obj = CarpetaMaterial.objects.filter(
                        pk=carpeta_id, docente=request.user
                    ).first()
                    carpeta_id = carpeta_obj.pk if carpeta_obj else None
                else:
                    carpeta_id = None

                orden = MaterialApoyo.objects.filter(
                    docente=request.user,
                    asignatura=asignacion.asignatura,
                    carpeta_id=carpeta_id,
                ).count()

                MaterialApoyo.objects.create(
                    docente=request.user,
                    grupo=asignacion.grupo,
                    asignatura=asignacion.asignatura,
                    carpeta_id=carpeta_id,
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo=tipo,
                    archivo=archivo,
                    url_externa=url_externa or None,
                    orden=orden,
                )
                messages.success(request, f'✅ "{titulo}" subido correctamente.')
                return redirect('material_apoyo')

    return render(request, 'docente/subir_material.html', {
        'asignaciones': asignaciones,
        'tipos':        MaterialApoyo.TIPOS,
    })


@docente_required
def detalle_material(request, pk):
    from academic.models import MaterialApoyo, ComentarioMaterial

    mat = get_object_or_404(MaterialApoyo, pk=pk, docente=request.user)

    if request.method == 'POST' and 'comentar' in request.POST:
        texto = request.POST.get('texto', '').strip()
        if texto:
            ComentarioMaterial.objects.create(material=mat, autor=request.user, texto=texto)
        return redirect('detalle_material', pk=pk)

    return render(request, 'docente/detalle_material.html', {
        'mat':         mat,
        'comentarios': mat.comentarios.select_related('autor').all(),
    })


@docente_required
def eliminar_material(request, pk):
    from academic.models import MaterialApoyo
    mat = get_object_or_404(MaterialApoyo, pk=pk, docente=request.user)
    if request.method == 'POST':
        mat.activo = False
        mat.save()
        messages.success(request, 'Material eliminado.')
    return redirect('material_apoyo')


@docente_required
def eliminar_carpeta(request, pk):
    from academic.models import CarpetaMaterial
    carpeta = get_object_or_404(CarpetaMaterial, pk=pk, docente=request.user)
    if request.method == 'POST':
        carpeta.materiales.update(carpeta=None)
        carpeta.delete()
        messages.success(request, 'Carpeta eliminada. Los materiales quedaron sin carpeta.')
    return redirect('material_apoyo')


@docente_required
def reordenar_material(request):
    import json
    from academic.models import MaterialApoyo
    if request.method == 'POST':
        try:
            ids = json.loads(request.body).get('ids', [])
            for i, pk in enumerate(ids):
                MaterialApoyo.objects.filter(pk=pk, docente=request.user).update(orden=i)
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})


@docente_required
def reordenar_carpetas(request):
    import json
    from academic.models import CarpetaMaterial
    if request.method == 'POST':
        try:
            ids = json.loads(request.body).get('ids', [])
            for i, pk in enumerate(ids):
                CarpetaMaterial.objects.filter(pk=pk, docente=request.user).update(orden=i)
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})


@docente_required
def carpetas_json(request):
    from academic.models import CarpetaMaterial
    grupo_id      = request.GET.get('grupo_id')
    asignatura_id = request.GET.get('asignatura_id')
    carpetas = CarpetaMaterial.objects.filter(
        docente=request.user,
        grupo_id=grupo_id,
        asignatura_id=asignatura_id,
    ).values('pk', 'nombre').order_by('orden', 'nombre')
    return JsonResponse({'carpetas': list(carpetas)})


# ─────────────────────────────────────────────────────────────────────────────
# PLANES DE CLASE
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def lista_planes(request):
    from django.core.paginator import Paginator

    grupos = Grupo.objects.filter(
        plantel=request.user.plantel, docentes=request.user
    )
    planes_qs = PlanClase.objects.filter(
        docente=request.user
    ).select_related('asignatura', 'grupo').prefetch_related('temas')

    paginator = Paginator(planes_qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'docente/planes/lista.html', {
        'planes':   page_obj,
        'page_obj': page_obj,
        'grupos':   grupos,
    })


@docente_required
def crear_plan(request):
    grupos = Grupo.objects.filter(
        plantel=request.user.plantel, docentes=request.user
    ).prefetch_related('asignaturas')
 
    if request.method == 'POST':
        grupo_id      = request.POST.get('grupo')
        asignatura_id = request.POST.get('asignatura')
        titulo        = request.POST.get('titulo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        periodo_tipo  = request.POST.get('periodo_tipo', 'MES')
        fecha_inicio  = request.POST.get('fecha_inicio')
        fecha_fin     = request.POST.get('fecha_fin')
        objetivo      = request.POST.get('objetivo_general', '').strip()
        competencias  = request.POST.get('competencias', '').strip()
 
        errors = []
        if not titulo:        errors.append('El título es obligatorio.')
        if not grupo_id:      errors.append('Selecciona un grupo.')
        if not asignatura_id: errors.append('Selecciona una asignatura.')
        if not fecha_inicio:  errors.append('La fecha de inicio es obligatoria.')
        if not fecha_fin:     errors.append('La fecha de fin es obligatoria.')
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            errors.append('La fecha de fin debe ser posterior al inicio.')
 
        for e in errors:
            messages.error(request, e)
 
        if not errors:
            # Validar grupo — debe pertenecer al plantel Y tener al docente asignado
            grupo = get_object_or_404(
                Grupo, pk=grupo_id,
                plantel=request.user.plantel,
                docentes=request.user,
            )
 
            # FIX advertencia 4: validar que la asignatura pertenezca
            # al grupo seleccionado (que ya está validado al plantel)
            asignatura = get_object_or_404(
                Asignatura, pk=asignatura_id,
                grupos=grupo,           # asignatura debe estar en ese grupo
            )
 
            plan = PlanClase.objects.create(
                docente=request.user,
                grupo=grupo,
                asignatura=asignatura,
                titulo=titulo,
                descripcion=descripcion,
                periodo_tipo=periodo_tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                objetivo_general=objetivo,
                competencias=competencias,
            )
            messages.success(request, f'Plan "{titulo}" creado. Ahora agrega los temas.')
            return redirect('docente_detalle_plan', pk=plan.pk)
 
    return render(request, 'docente/planes/crear.html', {'grupos': grupos})
 

@docente_required
def detalle_plan(request, pk):
    plan = get_object_or_404(PlanClase, pk=pk, docente=request.user)
    temas = plan.temas.all()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # ── Agregar tema ──
        if accion == 'agregar_tema':
            numero      = request.POST.get('numero')
            titulo      = request.POST.get('titulo_tema', '').strip()
            descripcion = request.POST.get('descripcion_tema', '').strip()
            fecha       = request.POST.get('fecha_tema') or None
            duracion    = request.POST.get('duracion_min', 50)
            recursos    = request.POST.get('recursos', '').strip()
            evaluacion  = request.POST.get('evaluacion', '').strip()

            if titulo and numero:
                TemaClase.objects.create(
                    plan=plan,
                    numero=int(numero),
                    titulo=titulo,
                    descripcion=descripcion,
                    fecha=fecha,
                    duracion_min=int(duracion),
                    recursos=recursos,
                    evaluacion=evaluacion,
                )
                messages.success(request, f'Sesión {numero} agregada.')
            else:
                messages.error(request, 'El número y título de la sesión son obligatorios.')
            return redirect('docente_detalle_plan', pk=pk)

        # ── Marcar tema completado ──
        if accion == 'toggle_completado':
            tema_id = request.POST.get('tema_id')
            tema = get_object_or_404(TemaClase, pk=tema_id, plan=plan)
            tema.completado = not tema.completado
            tema.save()
            return redirect('docente_detalle_plan', pk=pk)

        # ── Publicar/despublicar plan ──
        if accion == 'toggle_publicado':
            plan.publicado = not plan.publicado
            plan.save()
            estado = 'publicado' if plan.publicado else 'archivado'
            messages.success(request, f'Plan {estado}.')
            return redirect('docente_detalle_plan', pk=pk)

        # ── Eliminar tema ──
        if accion == 'eliminar_tema':
            tema_id = request.POST.get('tema_id')
            tema = get_object_or_404(TemaClase, pk=tema_id, plan=plan)
            tema.delete()
            messages.warning(request, 'Sesión eliminada.')
            return redirect('docente_detalle_plan', pk=pk)

    siguiente_numero = (temas.last().numero + 1) if temas.exists() else 1

    return render(request, 'docente/planes/detalle.html', {
        'plan':             plan,
        'temas':            temas,
        'siguiente_numero': siguiente_numero,
    })


@docente_required
def editar_plan(request, pk):
    plan   = get_object_or_404(PlanClase, pk=pk, docente=request.user)
    grupos = Grupo.objects.filter(
        plantel=request.user.plantel, docentes=request.user
    ).prefetch_related('asignaturas')

    if request.method == 'POST':
        plan.titulo           = request.POST.get('titulo', plan.titulo).strip()
        plan.descripcion      = request.POST.get('descripcion', '').strip()
        plan.periodo_tipo     = request.POST.get('periodo_tipo', plan.periodo_tipo)
        plan.fecha_inicio     = request.POST.get('fecha_inicio', plan.fecha_inicio)
        plan.fecha_fin        = request.POST.get('fecha_fin', plan.fecha_fin)
        plan.objetivo_general = request.POST.get('objetivo_general', '').strip()
        plan.competencias     = request.POST.get('competencias', '').strip()
        plan.save()
        messages.success(request, 'Plan actualizado.')
        return redirect('docente_detalle_plan', pk=pk)

    return render(request, 'docente/planes/editar.html', {
        'plan':   plan,
        'grupos': grupos,
    })


@docente_required
def eliminar_plan(request, pk):
    plan = get_object_or_404(PlanClase, pk=pk, docente=request.user)
    if request.method == 'POST':
        nombre = plan.titulo
        plan.delete()
        messages.warning(request, f'Plan "{nombre}" eliminado.')
        return redirect('docente_lista_planes')
    return redirect('docente_detalle_plan', pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTACIÓN PDF — usa ReportLab (pip install reportlab)
# ─────────────────────────────────────────────────────────────────────────────

def _pdf_styles():
    """Colores y fuentes comunes para todos los PDFs."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    styles  = getSampleStyleSheet()
    AZUL    = colors.HexColor('#10131c')
    ACCENT  = colors.HexColor('#4f6ef7')
    GRIS    = colors.HexColor('#f4f5f9')
    BORDE   = colors.HexColor('#e8eaf0')
    INK2    = colors.HexColor('#6b7280')
    OK      = colors.HexColor('#10b981')
    DANGER  = colors.HexColor('#e53e3e')
    WARN    = colors.HexColor('#f59e0b')

    titulo_style = ParagraphStyle(
        'TituloFRAY',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=AZUL,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        'SubFRAY',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=INK2,
        spaceAfter=12,
    )
    label_style = ParagraphStyle(
        'LabelFRAY',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=INK2,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'BodyFRAY',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=AZUL,
        leading=13,
    )
    return {
        'styles': styles,
        'AZUL': AZUL, 'ACCENT': ACCENT, 'GRIS': GRIS,
        'BORDE': BORDE, 'INK2': INK2, 'OK': OK,
        'DANGER': DANGER, 'WARN': WARN,
        'titulo': titulo_style, 'sub': sub_style,
        'label': label_style, 'body': body_style,
    }


def _pdf_header(canvas_obj, doc, plantel_nombre, titulo_reporte):
    """Encabezado y pie de página en todas las páginas."""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    AZUL   = colors.HexColor('#10131c')
    ACCENT = colors.HexColor('#4f6ef7')
    GRIS   = colors.HexColor('#f4f5f9')

    w, h = doc.pagesize
    canvas_obj.saveState()

    # Barra superior azul marino
    canvas_obj.setFillColor(AZUL)
    canvas_obj.rect(0, h - 1.4*cm, w, 1.4*cm, fill=1, stroke=0)

    # Logo FRAY
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.roundRect(0.5*cm, h - 1.2*cm, 0.9*cm, 0.9*cm, 3, fill=1, stroke=0)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.drawCentredString(0.95*cm, h - 0.82*cm, 'F')

    # Nombre plataforma
    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawString(1.6*cm, h - 0.82*cm, 'FRAY')

    # Plantel
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#9ca3af'))
    canvas_obj.drawString(3.2*cm, h - 0.82*cm, f'· {plantel_nombre}')

    # Título del reporte (derecha)
    canvas_obj.setFont('Helvetica-Bold', 9)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawRightString(w - 0.8*cm, h - 0.82*cm, titulo_reporte.upper())

    # Pie de página
    canvas_obj.setFillColor(GRIS)
    canvas_obj.rect(0, 0, w, 0.8*cm, fill=1, stroke=0)
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(colors.HexColor('#9ca3af'))
    canvas_obj.drawString(0.8*cm, 0.28*cm,
        f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}  ·  FRAY Sistema Escolar')
    canvas_obj.drawRightString(w - 0.8*cm, 0.28*cm, f'Página {canvas_obj.getPageNumber()}')

    canvas_obj.restoreState()


# ── PDF 1: Boleta de calificaciones por alumno ────────────────────────────────

@login_required
def pdf_boleta_alumno(request, alumno_pk):
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from users.models import User

    alumno = get_object_or_404(User, pk=alumno_pk, plantel=request.user.plantel, rol='ALUMNO')

    # Seguridad: docentes solo pueden ver boletas de alumnos en sus grupos
    if request.user.rol == 'DOCENTE':
        if not Grupo.objects.filter(
            plantel=request.user.plantel,
            docentes=request.user,
            alumnos=alumno,
        ).exists():
            messages.error(request, 'No tienes acceso a la boleta de este alumno.')
            return redirect('docente_mis_grupos')

    calificaciones = Calificacion.objects.filter(
        alumno=alumno
    ).select_related('asignatura').order_by('asignatura__nombre')

    s = _pdf_styles()
    plantel = request.user.plantel

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="boleta_{alumno.username}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        topMargin=2*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
    )

    def header(c, d):
        _pdf_header(c, d, plantel.nombre, 'Boleta de Calificaciones')

    elements = []

    # Datos del alumno
    elements.append(Paragraph(alumno.get_full_name(), s['titulo']))
    elements.append(Paragraph(
        f'Matrícula: {alumno.username}  ·  Grupo: {alumno.alumno_grupo or "Sin grupo"}  ·  '
        f'Estatus: {alumno.get_estatus_display()}',
        s['sub']
    ))
    elements.append(HRFlowable(width='100%', thickness=1, color=s['BORDE']))
    elements.append(Spacer(1, 0.3*cm))

    # Tabla de calificaciones
    data = [['ASIGNATURA', 'CALIFICACIÓN', 'ESTADO']]
    promedio_total = 0
    count = 0

    for cal in calificaciones:
        nota = float(cal.nota)
        promedio_total += nota
        count += 1
        estado = 'Aprobado' if nota >= 6 else 'Reprobado'
        data.append([
            cal.asignatura.nombre,
            f'{nota:.1f}',
            estado,
        ])

    if not calificaciones.exists():
        data.append(['Sin calificaciones registradas', '—', '—'])

    col_widths = [10*cm, 3*cm, 4*cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND',   (0,0), (-1,0), s['AZUL']),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 8),
        ('ALIGN',        (0,0), (-1,0), 'CENTER'),
        ('BOTTOMPADDING',(0,0), (-1,0), 8),
        ('TOPPADDING',   (0,0), (-1,0), 8),
        # Filas
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 9),
        ('ALIGN',        (1,1), (2,-1), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, s['GRIS']]),
        ('GRID',         (0,0), (-1,-1), 0.5, s['BORDE']),
        ('TOPPADDING',   (0,1), (-1,-1), 7),
        ('BOTTOMPADDING',(0,1), (-1,-1), 7),
    ]))

    # Color condicional en calificaciones
    for i, cal in enumerate(calificaciones, 1):
        nota = float(cal.nota)
        color = s['OK'] if nota >= 7 else (s['WARN'] if nota >= 6 else s['DANGER'])
        t.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), color)]))
        t.setStyle(TableStyle([('FONTNAME',  (1, i), (1, i), 'Helvetica-Bold')]))
        t.setStyle(TableStyle([('FONTSIZE',  (1, i), (1, i), 12)]))

    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    # Promedio general
    if count > 0:
        prom = promedio_total / count
        color_prom = s['OK'] if prom >= 7 else (s['WARN'] if prom >= 6 else s['DANGER'])
        prom_data = [['', 'PROMEDIO GENERAL', f'{prom:.2f}']]
        pt = Table(prom_data, colWidths=col_widths)
        pt.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), s['AZUL']),
            ('TEXTCOLOR',    (0,0), (-1,-1), colors.white),
            ('FONTNAME',     (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',     (0,0), (1,0),   9),
            ('FONTSIZE',     (2,0), (2,0),   14),
            ('TEXTCOLOR',    (2,0), (2,0),   color_prom),
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING',   (0,0), (-1,-1), 10),
            ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ]))
        elements.append(pt)

    doc.build(elements, onFirstPage=header, onLaterPages=header)
    return response


# ── PDF 2: Reporte de asistencia del grupo ───────────────────────────────────

@login_required
def pdf_asistencia_grupo(request, grupo_pk):
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from users.models import User

    grupo = get_object_or_404(Grupo, pk=grupo_pk, plantel=request.user.plantel)
    mes   = int(request.GET.get('mes', datetime.date.today().month))
    anio  = int(request.GET.get('anio', datetime.date.today().year))

    alumnos = User.objects.filter(
        rol='ALUMNO', alumno_grupo=grupo
    ).order_by('last_name', 'first_name')

    # Obtener fechas únicas del mes con asistencia registrada
    fechas = list(
        Asistencia.objects.filter(
            grupo=grupo, fecha__month=mes, fecha__year=anio
        ).values_list('fecha', flat=True).distinct().order_by('fecha')
    )

    s = _pdf_styles()
    plantel = request.user.plantel
    meses_nombres = ['', 'Enero','Febrero','Marzo','Abril','Mayo','Junio',
                     'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="asistencia_{grupo.nombre}_{meses_nombres[mes]}{anio}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        topMargin=2*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
    )

    def header(c, d):
        _pdf_header(c, d, plantel.nombre, 'Reporte de Asistencia')

    elements = []
    elements.append(Paragraph(f'Asistencia — {grupo}', s['titulo']))
    elements.append(Paragraph(
        f'{meses_nombres[mes]} {anio}  ·  {alumnos.count()} alumnos  ·  {len(fechas)} sesiones registradas',
        s['sub']
    ))
    elements.append(HRFlowable(width='100%', thickness=1, color=s['BORDE']))
    elements.append(Spacer(1, 0.3*cm))

    if not fechas:
        elements.append(Paragraph('No hay registros de asistencia para este mes.', s['body']))
        doc.build(elements, onFirstPage=header, onLaterPages=header)
        return response

    # Construir mapa de asistencia {alumno_id: {fecha: estado}}
    registros = Asistencia.objects.filter(
        grupo=grupo, fecha__month=mes, fecha__year=anio
    ).values('alumno_id', 'fecha', 'estado')

    mapa = {}
    for r in registros:
        mapa.setdefault(r['alumno_id'], {})[r['fecha']] = r['estado']

    # Cabecera: Nombre + fechas + totales
    header_row = ['#', 'Alumno'] + [f.strftime('%d') for f in fechas] + ['P', 'R', 'F', '%']
    data = [header_row]

    for i, alumno in enumerate(alumnos, 1):
        fila = [str(i), alumno.get_full_name()]
        p = r_cnt = f_cnt = 0
        for fecha in fechas:
            estado = mapa.get(alumno.pk, {}).get(fecha, '—')
            fila.append(estado)
            if estado == 'P': p += 1
            elif estado == 'R': r_cnt += 1
            elif estado == 'A': f_cnt += 1
        total = p + r_cnt + f_cnt
        pct = f'{int(p/total*100)}%' if total > 0 else '—'
        fila += [str(p), str(r_cnt), str(f_cnt), pct]
        data.append(fila)

    # Anchos de columna adaptativos
    n_fechas = len(fechas)
    w_nombre = 5*cm
    w_num    = 0.5*cm
    w_fecha  = max(0.55*cm, min(0.8*cm, 14*cm / max(n_fechas, 1)))
    w_tot    = 0.7*cm
    col_widths = [w_num, w_nombre] + [w_fecha]*n_fechas + [w_tot, w_tot, w_tot, w_tot]

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND',    (0,0), (-1,0), s['AZUL']),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 7),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',         (1,0), (1,-1), 'LEFT'),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1), (-1,-1), 7),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, s['GRIS']]),
        ('GRID',          (0,0), (-1,-1), 0.3, s['BORDE']),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]

    # Colorear celdas P/R/A
    for row_i, alumno in enumerate(alumnos, 1):
        for col_j, fecha in enumerate(fechas, 2):
            estado = mapa.get(alumno.pk, {}).get(fecha, '—')
            if estado == 'P':
                style.append(('TEXTCOLOR', (col_j, row_i), (col_j, row_i), s['OK']))
            elif estado == 'R':
                style.append(('TEXTCOLOR', (col_j, row_i), (col_j, row_i), s['WARN']))
            elif estado == 'A':
                style.append(('TEXTCOLOR', (col_j, row_i), (col_j, row_i), s['DANGER']))

    t.setStyle(TableStyle(style))
    elements.append(t)
    doc.build(elements, onFirstPage=header, onLaterPages=header)
    return response


# ── PDF 3: Cronograma / Temario del docente ───────────────────────────────────

@docente_required
def pdf_cronograma(request, plan_pk):
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib import colors

    plan  = get_object_or_404(PlanClase, pk=plan_pk, docente=request.user)
    temas = plan.temas.all()

    s = _pdf_styles()
    plantel = request.user.plantel

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="cronograma_{plan.pk}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        topMargin=2*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
    )

    def header(c, d):
        _pdf_header(c, d, plantel.nombre, 'Cronograma / Temario')

    elements = []

    # Encabezado del plan
    elements.append(Paragraph(plan.titulo, s['titulo']))
    elements.append(Paragraph(
        f'{plan.asignatura}  ·  {plan.grupo}  ·  '
        f'{plan.fecha_inicio.strftime("%d/%m/%Y")} – {plan.fecha_fin.strftime("%d/%m/%Y")}  ·  '
        f'Progreso: {plan.progreso}%',
        s['sub']
    ))
    elements.append(HRFlowable(width='100%', thickness=1, color=s['BORDE']))
    elements.append(Spacer(1, 0.3*cm))

    # Objetivo general
    if plan.objetivo_general:
        elements.append(Paragraph('OBJETIVO GENERAL', s['label']))
        elements.append(Paragraph(plan.objetivo_general, s['body']))
        elements.append(Spacer(1, 0.25*cm))

    # Competencias
    if plan.competencias:
        elements.append(Paragraph('COMPETENCIAS A DESARROLLAR', s['label']))
        elements.append(Paragraph(plan.competencias, s['body']))
        elements.append(Spacer(1, 0.4*cm))

    # Tabla de temas
    if temas.exists():
        elements.append(Paragraph('PLAN DE SESIONES', s['label']))
        elements.append(Spacer(1, 0.2*cm))

        data = [['#', 'TEMA / SESIÓN', 'FECHA', 'DURACIÓN', 'RECURSOS / EVALUACIÓN', 'EST.']]

        for tema in temas:
            fecha_str = tema.fecha.strftime('%d/%m/%Y') if tema.fecha else '—'
            recursos  = (tema.recursos or '') + ('\n' + tema.evaluacion if tema.evaluacion else '')
            estado    = '✓' if tema.completado else '○'
            desc      = tema.titulo
            if tema.descripcion:
                desc += f'\n{tema.descripcion}'
            data.append([
                str(tema.numero),
                Paragraph(desc, s['body']),
                fecha_str,
                f'{tema.duracion_min} min',
                Paragraph(recursos or '—', s['body']),
                estado,
            ])

        col_widths = [0.7*cm, 6*cm, 2*cm, 1.8*cm, 5*cm, 0.8*cm]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), s['AZUL']),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 7),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('ALIGN',         (1,0), (1,-1), 'LEFT'),
            ('ALIGN',         (4,0), (4,-1), 'LEFT'),
            ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',      (0,1), (-1,-1), 8),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, s['GRIS']]),
            ('GRID',          (0,0), (-1,-1), 0.3, s['BORDE']),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ]))

        # Colorear estado completado
        for i, tema in enumerate(temas, 1):
            color = s['OK'] if tema.completado else s['INK2']
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (5, i), (5, i), color),
                ('FONTNAME',  (5, i), (5, i), 'Helvetica-Bold'),
                ('FONTSIZE',  (5, i), (5, i), 11),
            ]))

        elements.append(t)
    else:
        elements.append(Paragraph('Este plan no tiene sesiones registradas aún.', s['body']))

    # Firma
    elements.append(Spacer(1, 1.5*cm))
    firma_data = [
        ['Docente:', plan.docente.get_full_name(), 'Firma:', '___________________________'],
    ]
    ft = Table(firma_data, colWidths=[2*cm, 6*cm, 2*cm, 6*cm])
    ft.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (0,-1), s['INK2']),
        ('TEXTCOLOR', (2,0), (2,-1), s['INK2']),
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0), (2,-1), 'Helvetica-Bold'),
    ]))
    elements.append(ft)

    doc.build(elements, onFirstPage=header, onLaterPages=header)
    return response
# ─────────────────────────────────────────────────────────────────────────────
# EXPORTACIÓN PDF
# Agregar al final de docente/views.py
# ─────────────────────────────────────────────────────────────────────────────

@docente_required
def pdf_boleta_grupo(request, grupo_id):
    from academic.models import Grupo, Calificacion, EntregaTarea, EntregaActividad
    from django.http import HttpResponse
    from .pdf_utils import generar_pdf_boleta

    grupo = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, grupo=grupo)
        .select_related('asignatura')
    )
    if not asignaciones.exists():
        messages.error(request, 'No tienes acceso a este grupo.')
        return redirect('docente_boleta')

    asignaturas = [a.asignatura for a in asignaciones]
    alumnos     = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

    filas = []
    for alumno in alumnos:
        cols = []
        for asig in asignaturas:
            prom_tareas = EntregaTarea.objects.filter(
                alumno=alumno, tarea__asignatura=asig,
                tarea__grupo=grupo, calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            prom_actividades = EntregaActividad.objects.filter(
                alumno=alumno, actividad__asignatura=asig,
                actividad__grupo=grupo, calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            cal_manual = Calificacion.objects.filter(
                alumno=alumno, asignatura=asig, grupo=grupo, tipo='MANUAL',
            ).first()

            valores = [v for v in [
                prom_tareas, prom_actividades,
                cal_manual.nota if cal_manual else None,
            ] if v is not None]
            promedio_final = round(sum(valores) / len(valores), 2) if valores else None

            cols.append({
                'asignatura':  asig,
                'prom_tareas': round(float(prom_tareas), 2) if prom_tareas else None,
                'prom_activ':  round(float(prom_actividades), 2) if prom_actividades else None,
                'manual':      float(cal_manual.nota) if cal_manual else None,
                'final':       promedio_final,
            })
        filas.append({'alumno': alumno, 'cols': cols})

    buffer = generar_pdf_boleta(grupo, asignaturas, filas, request.user)

    nombre_archivo = f"boleta_{grupo.nombre.replace(' ', '_')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


@docente_required
def pdf_concentrado(request, grupo_id):
    from academic.models import Grupo, Calificacion, EntregaTarea, EntregaActividad
    from django.http import HttpResponse
    from .pdf_utils import generar_pdf_concentrado

    grupo = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, grupo=grupo)
        .select_related('asignatura')
    )
    if not asignaciones.exists():
        messages.error(request, 'No tienes acceso a este grupo.')
        return redirect('docente_concentrado')

    asignaturas = [a.asignatura for a in asignaciones]
    alumnos     = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

    filas = []
    for alumno in alumnos:
        cols = []
        for asig in asignaturas:
            prom_tareas = EntregaTarea.objects.filter(
                alumno=alumno, tarea__asignatura=asig,
                tarea__grupo=grupo, calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            prom_activ = EntregaActividad.objects.filter(
                alumno=alumno, actividad__asignatura=asig,
                actividad__grupo=grupo, calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            cal_manual = Calificacion.objects.filter(
                alumno=alumno, asignatura=asig, grupo=grupo, tipo='MANUAL',
            ).first()

            valores = [v for v in [
                prom_tareas, prom_activ,
                cal_manual.nota if cal_manual else None,
            ] if v is not None]
            cols.append(round(sum(valores) / len(valores), 2) if valores else None)

        valores_fila     = [c for c in cols if c is not None]
        promedio_general = round(sum(valores_fila) / len(valores_fila), 2) if valores_fila else None
        filas.append({'alumno': alumno, 'cols': cols, 'promedio_general': promedio_general})

    buffer = generar_pdf_concentrado(grupo, asignaturas, filas, request.user)

    nombre_archivo = f"concentrado_{grupo.nombre.replace(' ', '_')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


@docente_required
def pdf_asistencia(request, grupo_id, asignatura_id):
    from academic.models import Grupo, Asignatura, Asistencia
    from django.http import HttpResponse
    from .pdf_utils import generar_pdf_asistencia
    from datetime import date

    grupo      = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)

    # Verificar que el docente tiene acceso
    tiene_acceso = DocenteGrupo.objects.filter(
        docente=request.user, activo=True,
        grupo=grupo, asignatura=asignatura,
    ).exists()
    if not tiene_acceso:
        messages.error(request, 'No tienes acceso a este grupo/asignatura.')
        return redirect('docente_lista_asistencia')

    # Mes a exportar (parámetro GET, default mes actual)
    mes_str = request.GET.get('mes', '')
    try:
        from datetime import datetime
        fecha = datetime.strptime(mes_str, '%Y-%m').date()
    except (ValueError, TypeError):
        fecha = date.today()

    alumnos = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

    from django.db.models import Count, Q
    resumen_qs = Asistencia.objects.filter(
        grupo=grupo, asignatura=asignatura,
        fecha__month=fecha.month, fecha__year=fecha.year,
    ).values('alumno_id').annotate(
        presentes=Count('id', filter=Q(estado='P')),
        ausentes =Count('id', filter=Q(estado='A')),
        retardos =Count('id', filter=Q(estado='R')),
    )
    resumen = {r['alumno_id']: r for r in resumen_qs}

    filas = []
    for alumno in alumnos:
        res = resumen.get(alumno.pk, {'presentes': 0, 'ausentes': 0, 'retardos': 0})
        filas.append({
            'alumno':    alumno,
            'presentes': res['presentes'],
            'retardos':  res['retardos'],
            'ausentes':  res['ausentes'],
        })

    buffer = generar_pdf_asistencia(grupo, asignatura, filas, fecha, request.user)

    nombre_archivo = f"asistencia_{grupo.nombre.replace(' ','_')}_{fecha.strftime('%Y-%m')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response

@docente_required
def parcial(request):
    from users.models import DocenteGrupo
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/parcial.html', {
        'asignaciones': asignaciones,
    })


@docente_required
def parcial_config(request, grupo_id, asig_id):
    from academic.models import Grupo, Asignatura, ConfigEvaluacion
    from users.models import DocenteGrupo

    grupo      = get_object_or_404(Grupo, pk=grupo_id)
    asignatura = get_object_or_404(Asignatura, pk=asig_id)

    # Verificar que el docente tiene esa asignación
    asignacion = DocenteGrupo.objects.filter(
        docente=request.user, grupo=grupo, asignatura=asignatura, activo=True
    ).first()
    if not asignacion:
        messages.error(request, 'No tienes acceso a ese grupo/asignatura.')
        return redirect('docente_parcial')

    config, _ = ConfigEvaluacion.objects.get_or_create(
        docente=request.user, grupo=grupo, asignatura=asignatura,
        defaults={
            'pct_tareas': 20, 'pct_actividades': 20,
            'pct_asistencia': 10, 'pct_examen': 30, 'pct_proyecto': 20,
        }
    )

    if request.method == 'POST':
        try:
            config.pct_tareas      = request.POST.get('pct_tareas', 0)
            config.pct_actividades = request.POST.get('pct_actividades', 0)
            config.pct_asistencia  = request.POST.get('pct_asistencia', 0)
            config.pct_examen      = request.POST.get('pct_examen', 0)
            config.pct_proyecto    = request.POST.get('pct_proyecto', 0)
            config.save()
            messages.success(request, 'Configuración de evaluación guardada.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('docente_parcial_detalle', grupo_id=grupo_id, asig_id=asig_id)

    return render(request, 'docente/parcial_config.html', {
        'grupo':      grupo,
        'asignatura': asignatura,
        'config':     config,
    })


@docente_required
def parcial_detalle(request, grupo_id, asig_id):
    from academic.models import (
        Grupo, Asignatura, ConfigEvaluacion, EvaluacionParcial,
        EntregaTarea, EntregaActividad, Asistencia,
        Tarea, Actividad, BoletaParcial
    )
    from users.models import DocenteGrupo
    from django.db.models import Avg, Count, Q

    grupo      = get_object_or_404(Grupo, pk=grupo_id)
    asignatura = get_object_or_404(Asignatura, pk=asig_id)

    asignacion = DocenteGrupo.objects.filter(
        docente=request.user, grupo=grupo, asignatura=asignatura, activo=True
    ).first()
    if not asignacion:
        messages.error(request, 'No tienes acceso a ese grupo/asignatura.')
        return redirect('docente_parcial')

    config, _ = ConfigEvaluacion.objects.get_or_create(
        docente=request.user, grupo=grupo, asignatura=asignatura,
        defaults={
            'pct_tareas': 20, 'pct_actividades': 20,
            'pct_asistencia': 10, 'pct_examen': 30, 'pct_proyecto': 20,
        }
    )

    # Parcial seleccionado (1-4)
    parcial_num = int(request.GET.get('parcial', 1))
    if parcial_num not in [1, 2, 3, 4]:
        parcial_num = 1

    alumnos = grupo.alumnos.filter(
        estatus='ACTIVO', rol='ALUMNO'
    ).order_by('last_name', 'first_name')

    tareas = Tarea.objects.filter(
        grupo=grupo, asignatura=asignatura,
        docente=request.user, publicada=True
    ).order_by('creada_en')

    actividades = Actividad.objects.filter(
        grupo=grupo, asignatura=asignatura,
        docente=request.user, publicada=True
    ).order_by('creada_en')

    # ── Guardar examen/proyecto manual ───────────────────────────────────────
    if request.method == 'POST' and 'guardar_notas' in request.POST:
        for alumno in alumnos:
            for rubro in ('EXAMEN', 'PROYECTO'):
                key = f'{rubro.lower()}_{alumno.pk}'
                val = request.POST.get(key, '').strip()
                if val:
                    try:
                        nota = float(val)
                        if 0 <= nota <= 10:
                            EvaluacionParcial.objects.update_or_create(
                                alumno=alumno, grupo=grupo,
                                asignatura=asignatura, rubro=rubro,
                                defaults={'nota': nota, 'docente': request.user}
                            )
                    except ValueError:
                        pass
        messages.success(request, 'Calificaciones guardadas.')
        return redirect(f"{request.path}?parcial={parcial_num}")

    # ── Publicar boleta del parcial ───────────────────────────────────────────
    if request.method == 'POST' and 'publicar_parcial' in request.POST:
        publicar = request.POST.get('publicar_parcial') == '1'
        count = 0
        for alumno in alumnos:
            boleta = BoletaParcial.objects.filter(
                alumno=alumno, grupo=grupo,
                asignatura=asignatura, parcial=parcial_num
            ).first()
            if boleta:
                boleta.publicada    = publicar
                boleta.publicada_en = timezone.now() if publicar else None
                boleta.save()
                count += 1
        estado = 'publicadas' if publicar else 'ocultadas'
        messages.success(request, f'Boletas del Parcial {parcial_num} {estado} para {count} alumnos.')
        return redirect(f"{request.path}?parcial={parcial_num}")

    # ── Calcular y guardar boleta ─────────────────────────────────────────────
    if request.method == 'POST' and 'calcular_parcial' in request.POST:
        guardadas = 0
        for alumno in alumnos:
            # Promedios tareas
            vals_t = list(EntregaTarea.objects.filter(
                tarea__in=tareas, alumno=alumno,
                calificacion__isnull=False
            ).values_list('calificacion', flat=True))
            prom_t = round(sum(float(v) for v in vals_t) / len(vals_t), 2) if vals_t else None

            # Promedios actividades
            vals_a = list(EntregaActividad.objects.filter(
                actividad__in=actividades, alumno=alumno,
                calificacion__isnull=False
            ).values_list('calificacion', flat=True))
            prom_a = round(sum(float(v) for v in vals_a) / len(vals_a), 2) if vals_a else None

            # Asistencia
            total_clases = Asistencia.objects.filter(
                alumno=alumno, grupo=grupo, asignatura=asignatura
            ).count()
            presentes = Asistencia.objects.filter(
                alumno=alumno, grupo=grupo, asignatura=asignatura, estado='P'
            ).count()
            pct_asist  = round((presentes / total_clases) * 100, 1) if total_clases > 0 else 0
            nota_asist = round(pct_asist / 10, 2)

            # Examen y proyecto
            examen   = EvaluacionParcial.objects.filter(
                alumno=alumno, grupo=grupo, asignatura=asignatura, rubro='EXAMEN'
            ).first()
            proyecto = EvaluacionParcial.objects.filter(
                alumno=alumno, grupo=grupo, asignatura=asignatura, rubro='PROYECTO'
            ).first()
            nota_ex  = float(examen.nota)   if examen   else None
            nota_pr  = float(proyecto.nota) if proyecto else None

            # Ponderación
            def pond(nota, pct):
                return (nota * float(pct) / 100) if nota is not None else 0

            total_pct  = 0
            cal_final  = 0

            if prom_t is not None:
                cal_final += pond(prom_t, config.pct_tareas)
                total_pct += float(config.pct_tareas)
            if prom_a is not None:
                cal_final += pond(prom_a, config.pct_actividades)
                total_pct += float(config.pct_actividades)
            if total_clases > 0:
                cal_final += pond(nota_asist, config.pct_asistencia)
                total_pct += float(config.pct_asistencia)
            if nota_ex is not None:
                cal_final += pond(nota_ex, config.pct_examen)
                total_pct += float(config.pct_examen)
            if nota_pr is not None:
                cal_final += pond(nota_pr, config.pct_proyecto)
                total_pct += float(config.pct_proyecto)

            if total_pct > 0:
                if total_pct < 100:
                    cal_final = round(cal_final * 100 / total_pct, 2)
                else:
                    cal_final = round(cal_final, 2)

                BoletaParcial.objects.update_or_create(
                    alumno=alumno, grupo=grupo,
                    asignatura=asignatura, parcial=parcial_num,
                    defaults={
                        'docente':           request.user,
                        'nota_tareas':       prom_t,
                        'nota_actividades':  prom_a,
                        'nota_asistencia':   nota_asist,
                        'nota_examen':       nota_ex,
                        'nota_proyecto':     nota_pr,
                        'calificacion_final': cal_final,
                        'publicada':         False,
                    }
                )
                guardadas += 1

        messages.success(request, f'✅ Calificación del Parcial {parcial_num} calculada para {guardadas} alumnos. Revisa y publica cuando estés listo.')
        return redirect(f"{request.path}?parcial={parcial_num}")

    # ── Construir filas ───────────────────────────────────────────────────────
    boletas_existentes = {
        b.alumno_id: b
        for b in BoletaParcial.objects.filter(
            grupo=grupo, asignatura=asignatura, parcial=parcial_num
        )
    }

    filas = []
    for alumno in alumnos:
        vals_t = list(EntregaTarea.objects.filter(
            tarea__in=tareas, alumno=alumno, calificacion__isnull=False
        ).values_list('calificacion', flat=True))
        prom_t = round(sum(float(v) for v in vals_t) / len(vals_t), 2) if vals_t else None

        vals_a = list(EntregaActividad.objects.filter(
            actividad__in=actividades, alumno=alumno, calificacion__isnull=False
        ).values_list('calificacion', flat=True))
        prom_a = round(sum(float(v) for v in vals_a) / len(vals_a), 2) if vals_a else None

        total_clases = Asistencia.objects.filter(
            alumno=alumno, grupo=grupo, asignatura=asignatura
        ).count()
        presentes    = Asistencia.objects.filter(
            alumno=alumno, grupo=grupo, asignatura=asignatura, estado='P'
        ).count()
        pct_asist    = round((presentes / total_clases) * 100, 1) if total_clases > 0 else 0

        examen   = EvaluacionParcial.objects.filter(
            alumno=alumno, grupo=grupo, asignatura=asignatura, rubro='EXAMEN'
        ).first()
        proyecto = EvaluacionParcial.objects.filter(
            alumno=alumno, grupo=grupo, asignatura=asignatura, rubro='PROYECTO'
        ).first()

        boleta = boletas_existentes.get(alumno.pk)

        filas.append({
            'alumno':          alumno,
            'prom_tareas':     prom_t,
            'prom_actividades': prom_a,
            'pct_asistencia':  pct_asist,
            'nota_examen':     float(examen.nota)   if examen   else None,
            'nota_proyecto':   float(proyecto.nota) if proyecto else None,
            'boleta':          boleta,
            'calificacion_final': float(boleta.calificacion_final) if boleta else None,
            'publicada':       boleta.publicada if boleta else False,
        })

    parcial_publicado = all(f['publicada'] for f in filas if f['boleta'])
    total_con_boleta  = sum(1 for f in filas if f['boleta'])

    return render(request, 'docente/parcial_detalle.html', {
        'grupo':             grupo,
        'asignatura':        asignatura,
        'config':            config,
        'tareas':            tareas,
        'actividades':       actividades,
        'filas':             filas,
        'parcial_num':       parcial_num,
        'parciales':         [1, 2, 3, 4],
        'parcial_publicado': parcial_publicado,
        'total_con_boleta':  total_con_boleta,
        'total_alumnos':     alumnos.count(),
    })