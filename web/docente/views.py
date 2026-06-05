# docente/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from users.models import DocenteGrupo
from django.utils import timezone
from django.db.models import F, Q, Avg, Count, Case, When, IntegerField
import cloudinary
import requests as req

def docente_required(view_func):
    """Decorador: solo docentes pueden acceder."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.rol != 'DOCENTE':
            messages.error(request, 'No tienes permiso para acceder a esa sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Mi Espacio ────────────────────────────────────────────────────────────────

@docente_required
def mis_grupos(request):
    from academic.models import Grupo
    grupos = Grupo.objects.filter(
        plantel=request.user.plantel,
        docentes=request.user
    ).prefetch_related('alumnos', 'asignaturas')
    
    return render(request, 'docente/mis_grupos.html', {
        'grupos': grupos,
    })

@docente_required
def mi_horario(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/mi_horario.html', {
        'asignaciones': asignaciones,
    })


# ── Clase ───────────────────────────────────────────────────────────────────


@docente_required
def lista_asistencia(request):
    from academic.models import Asistencia, Grupo, Asignatura
    from users.models import DocenteGrupo
    from datetime import date

    # Solo asignaciones CON asignatura definida (excluye tutorías sin materia)
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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

    grupo       = None
    asignatura  = None
    filas       = []
    ya_guardado = False

    if grupo_id and asignatura_id:
        # Verificar que esta combinación le pertenece al docente
        asignacion = asignaciones.filter(
            grupo_id=grupo_id,
            asignatura_id=asignatura_id
        ).first()

        if not asignacion:
            messages.error(request, 'No tienes permiso para ese grupo/asignatura.')
            return redirect('lista_asistencia')

        grupo      = asignacion.grupo
        asignatura = asignacion.asignatura

        # Alumnos ACTIVOS del grupo (via alumno_grupo FK)
        alumnos = (
            grupo.alumnos
            .filter(estatus='ACTIVO', rol='ALUMNO')
            .order_by('last_name', 'first_name')
        )

        # Asistencias ya guardadas para este día
        registros_hoy = {
            r.alumno_id: r.estado
            for r in Asistencia.objects.filter(
                grupo=grupo,
                asignatura=asignatura,
                fecha=fecha,
            )
        }
        ya_guardado = bool(registros_hoy)

        # Resumen del mes
        from django.db.models import Count, Q
        resumen_qs = Asistencia.objects.filter(
            grupo=grupo,
            asignatura=asignatura,
            fecha__month=fecha.month,
            fecha__year=fecha.year,
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

        # Guardar asistencia
        if request.method == 'POST' and 'guardar' in request.POST:
            for fila in filas:
                alumno = fila['alumno']
                estado = request.POST.get(f'estado_{alumno.pk}', 'A')
                if estado not in ('P', 'A', 'R'):
                    estado = 'A'
                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    grupo=grupo,
                    asignatura=asignatura,
                    fecha=fecha,
                    defaults={'estado': estado},
                )
            messages.success(
                request,
                f'✅ Asistencia del {fecha.strftime("%d/%m/%Y")} guardada.'
            )
            return redirect(
                f"{request.path}?grupo_id={grupo_id}&asignatura_id={asignatura_id}&fecha={fecha}"
            )

    from django.utils import timezone
    return render(request, 'docente/asistencia.html', {
        'asignaciones': asignaciones,
        'grupo':        grupo,
        'asignatura':   asignatura,
        'filas':        filas,
        'fecha':        fecha,
        'ya_guardado':  ya_guardado,
        'hoy':          timezone.now().date(),
    })
@docente_required
def tareas(request):
    from academic.models import Tarea, EntregaTarea
    from users.models import DocenteGrupo

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
        .select_related('grupo', 'asignatura')
    )

    # Filtros
    grupo_id      = request.GET.get('grupo_id')
    asignatura_id = request.GET.get('asignatura_id')

    tareas_qs = Tarea.objects.filter(docente=request.user).select_related('grupo', 'asignatura')
    if grupo_id:
        tareas_qs = tareas_qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        tareas_qs = tareas_qs.filter(asignatura_id=asignatura_id)

    # Anotar conteo de entregas por tarea
    from django.db.models import Count
    tareas_qs = tareas_qs.annotate(
        total_entregas=Count('entregas'),
        entregas_calificadas=Count('entregas', filter=Q(entregas__estado='CALIFICADA')),
    )

    return render(request, 'docente/tareas.html', {
        'asignaciones':  asignaciones,
        'tareas':        tareas_qs,
        'grupo_id':      grupo_id,
        'asignatura_id': asignatura_id,
    })


@docente_required
def crear_tarea(request):
    from academic.models import Tarea
    from users.models import DocenteGrupo

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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
            # Verificar que el docente tiene esa asignación
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
                )
                messages.success(request, f'✅ Tarea "{titulo}" creada correctamente.')
                return redirect('detalle_tarea', pk=tarea.pk)

    return render(request, 'docente/crear_tarea.html', {
        'asignaciones': asignaciones,
    })

def fix_pdf_url(url):
    url = url.replace('http://', 'https://').replace('/image/upload/', '/raw/upload/')
    if not url.endswith('.pdf'):
        url += '.pdf'
    return url

@docente_required
def detalle_tarea(request, pk):
    from academic.models import Tarea, EntregaTarea, ComentarioTarea
    from django.utils import timezone

    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)

    # Alumnos del grupo
    alumnos = tarea.grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO')

    # Entregas existentes {alumno_id: entrega}
    entregas = {e.alumno_id: e for e in tarea.entregas.select_related('alumno').all()}

    # Construir filas
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

    # Calificar entrega
    if request.method == 'POST' and 'calificar' in request.POST:
        entrega_id  = request.POST.get('entrega_id')
        calificacion = request.POST.get('calificacion')
        feedback    = request.POST.get('feedback', '').strip()
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

    # Comentar
    if request.method == 'POST' and 'comentar' in request.POST:
        texto = request.POST.get('texto', '').strip()
        if texto:
            ComentarioTarea.objects.create(tarea=tarea, autor=request.user, texto=texto)
        return redirect('detalle_tarea', pk=pk)

    comentarios = tarea.comentarios.select_related('autor').all()
    total_alumnos = alumnos.count()
    total_entregaron = len([f for f in filas if f['entrega']])
    total_calificadas = len([f for f in filas if f['estado'] == 'CALIFICADA'])
    total_pendientes = total_alumnos - total_entregaron
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
    from academic.models import Tarea, EntregaTarea
    import requests as req

    if tipo == 'tarea':
        obj = get_object_or_404(Tarea, pk=pk, docente=request.user)
        public_id = str(obj.archivo) if obj.archivo else None
    else:
        obj = get_object_or_404(EntregaTarea, pk=pk)
        public_id = str(obj.archivo) if obj.archivo else None

    if not public_id:
        return redirect('docente_tareas')

    from django.conf import settings
    cloud = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
    if not public_id.endswith('.pdf'):
        public_id += '.pdf'
    url = f'https://res.cloudinary.com/{cloud}/raw/upload/{public_id}'

    r = req.get(url)
    from django.http import HttpResponse
    response = HttpResponse(r.content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="documento.pdf"'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@docente_required
def eliminar_tarea(request, pk):
    from academic.models import Tarea
    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada.')
    return redirect('docente_tareas')


@docente_required
def actividades(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/actividades.html', {
        'asignaciones': asignaciones,
    })


# ── Calificaciones ────────────────────────────────────────────────────────────

@docente_required
def calificar_tareas(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/calificar_tareas.html', {
        'asignaciones': asignaciones,
    })


@docente_required
def calificar_actividades(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/calificar_actividades.html', {
        'asignaciones': asignaciones,
    })


@docente_required
def boleta(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/boleta.html', {
        'asignaciones': asignaciones,
    })


# ── Contenido ─────────────────────────────────────────────────────────────────

@docente_required
def material_apoyo(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/material.html', {
        'asignaciones': asignaciones,
    })


@docente_required
def subir_contenido(request):
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    return render(request, 'docente/contenido.html', {
        'asignaciones': asignaciones,
    })