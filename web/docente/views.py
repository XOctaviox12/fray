# docente/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from users.models import DocenteGrupo
from django.utils import timezone
from django.db.models import F, Q, Avg, Count, Case, When, IntegerField
import cloudinary
import requests as req
from django.http import JsonResponse

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
    from academic.models import Tarea
    from django.utils import timezone

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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
                    publicada=request.POST.get('publicada') == '1', 
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
    if request.method == 'POST' and 'toggle_publicar' in request.POST:
        tarea.publicada = not tarea.publicada
        tarea.save()
        estado = 'publicada' if tarea.publicada else 'guardada como borrador'
        messages.success(request, f'Tarea {estado} correctamente.')
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
def editar_tarea(request, pk):
    from academic.models import Tarea

    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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
        'tarea':        tarea,
        'asignaciones': asignaciones,
    })

@docente_required
def eliminar_tarea(request, pk):
    from academic.models import Tarea
    tarea = get_object_or_404(Tarea, pk=pk, docente=request.user)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada.')
    return redirect('docente_tareas')


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


@docente_required
def actividades(request):
    from academic.models import Actividad
    from users.models import DocenteGrupo
    from django.utils import timezone

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
        .select_related('grupo', 'asignatura')
    )

    grupo_id      = request.GET.get('grupo_id')
    asignatura_id = request.GET.get('asignatura_id')

    qs = Actividad.objects.filter(docente=request.user).select_related('grupo', 'asignatura')
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        qs = qs.filter(asignatura_id=asignatura_id)

    qs = qs.annotate(total_entregas=Count('entregas'))
    ahora = timezone.now()

    activas   = qs.filter(publicada=True,  fecha_entrega__gte=ahora)
    vencidas  = qs.filter(publicada=True,  fecha_entrega__lt=ahora)
    borradores = qs.filter(publicada=False)

    return render(request, 'docente/actividades.html', {
        'asignaciones':  asignaciones,
        'activas':       activas,
        'vencidas':      vencidas,
        'borradores':    borradores,
        'grupo_id':      grupo_id,
        'asignatura_id': asignatura_id,
    })

@docente_required
def crear_actividad(request):
    from academic.models import Actividad, PreguntaActividad, OpcionRespuesta
    from users.models import DocenteGrupo

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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

                # Guardar preguntas si es MULTIPLE o ABIERTA
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
                            opciones    = request.POST.getlist(f'opcion_texto_{i}')
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

    return render(request, 'docente/crear_actividad.html', {
        'asignaciones': asignaciones,
    })


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
    # Publicar/despublicar
    if request.method == 'POST' and 'toggle_publicar' in request.POST:
        actividad.publicada = not actividad.publicada
        actividad.publicada_en = timezone.now() if actividad.publicada else None
        actividad.save()
        estado = 'publicada' if actividad.publicada else 'despublicada'
        messages.success(request, f'Actividad {estado} correctamente.')
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
def eliminar_actividad(request, pk):
    from academic.models import Actividad
    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)
    if request.method == 'POST':
        actividad.delete()
        messages.success(request, 'Actividad eliminada.')
    return redirect('docente_actividades')

@docente_required
def editar_actividad(request, pk):
    from academic.models import Actividad, PreguntaActividad, OpcionRespuesta
    from users.models import DocenteGrupo

    actividad = get_object_or_404(Actividad, pk=pk, docente=request.user)

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
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

            # Actualizar preguntas solo si el tipo lo permite
            if actividad.tipo in ('MULTIPLE', 'ABIERTA'):
                # Borrar preguntas existentes y recrear
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
        'actividad':    actividad,
        'asignaciones': asignaciones,
        'preguntas':    preguntas,
    })

# ── Material de Apoyo ─────────────────────────────────────────────────────────

@docente_required
def material_apoyo(request):
    from academic.models import MaterialApoyo, CarpetaMaterial
    from users.models import DocenteGrupo
    from django.db.models import Count

    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, asignatura__isnull=False)
        .select_related('grupo', 'asignatura')
    )

    grupo_id      = request.GET.get('grupo_id', '')
    asignatura_id = request.GET.get('asignatura_id', '')
    tipo_filtro   = request.GET.get('tipo', '')
    carpeta_id    = request.GET.get('carpeta_id', '')
    q             = request.GET.get('q', '').strip()

    # Base queryset — solo sus grupos/asignaturas
    qs = MaterialApoyo.objects.filter(
        docente=request.user, activo=True
    ).select_related('grupo', 'asignatura', 'carpeta')

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

    # Carpetas disponibles según filtro actual
    carpetas_qs = CarpetaMaterial.objects.filter(docente=request.user)
    if grupo_id:
        carpetas_qs = carpetas_qs.filter(grupo_id=grupo_id)
    if asignatura_id:
        carpetas_qs = carpetas_qs.filter(asignatura_id=asignatura_id)

    carpetas_qs = carpetas_qs.annotate(total=Count('materiales'))

    # Agrupar materiales por carpeta para la vista
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
                # Crear carpeta nueva si se especificó
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

                # Orden: último de su carpeta/asignatura
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

    comentarios = mat.comentarios.select_related('autor').all()
    return render(request, 'docente/detalle_material.html', {
        'mat':        mat,
        'comentarios': comentarios,
    })


@docente_required
def reordenar_material(request):
    """AJAX — recibe lista de PKs en orden nuevo."""
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
    """AJAX — reordena carpetas."""
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
        # Mover materiales a sin carpeta
        carpeta.materiales.update(carpeta=None)
        carpeta.delete()
        messages.success(request, 'Carpeta eliminada. Los materiales quedaron sin carpeta.')
    return redirect('material_apoyo')
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

@docente_required
def boleta(request):
    from users.models import DocenteGrupo
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo')
        .values('grupo__pk', 'grupo__nombre')
        .distinct()
    )
    return render(request, 'docente/boleta.html', {'grupos': asignaciones})


@docente_required
def boleta_grupo(request, grupo_id):
    from academic.models import Grupo, Calificacion, EntregaTarea, EntregaActividad
    from users.models import DocenteGrupo
    from django.db.models import Avg

    grupo = get_object_or_404(Grupo, pk=grupo_id)

    # Verificar que el docente pertenece a este grupo
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True, grupo=grupo)
        .select_related('asignatura')
    )
    if not asignaciones.exists():
        messages.error(request, 'No tienes acceso a este grupo.')
        return redirect('docente_boleta')

    asignaturas = [a.asignatura for a in asignaciones]
    alumnos = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

    # Guardar calificación manual
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('cal_'):
                _, alumno_id, asig_id = key.split('_')
                try:
                    nota = float(value)
                    if 0 <= nota <= 10:
                        Calificacion.objects.update_or_create(
                            alumno_id=alumno_id,
                            asignatura_id=asig_id,
                            grupo=grupo,
                            tipo='MANUAL',
                            defaults={'nota': nota, 'docente': request.user}
                        )
                except (ValueError, TypeError):
                    pass
        messages.success(request, 'Calificaciones guardadas.')
        return redirect('docente_boleta_grupo', grupo_id=grupo_id)

    # Construir tabla de calificaciones
    filas = []
    for alumno in alumnos:
        cols = []
        for asig in asignaturas:
            # Promedio tareas
            prom_tareas = EntregaTarea.objects.filter(
                alumno=alumno,
                tarea__asignatura=asig,
                tarea__grupo=grupo,
                calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            # Promedio actividades
            prom_actividades = EntregaActividad.objects.filter(
                alumno=alumno,
                actividad__asignatura=asig,
                actividad__grupo=grupo,
                calificacion__isnull=False,
            ).aggregate(p=Avg('calificacion'))['p']

            # Calificación manual
            cal_manual = Calificacion.objects.filter(
                alumno=alumno,
                asignatura=asig,
                grupo=grupo,
                tipo='MANUAL',
            ).first()

            # Promedio final
            valores = [v for v in [prom_tareas, prom_actividades, cal_manual.nota if cal_manual else None] if v is not None]
            promedio_final = round(sum(valores) / len(valores), 2) if valores else None

            cols.append({
                'asignatura':    asig,
                'prom_tareas':   round(float(prom_tareas), 2) if prom_tareas else None,
                'prom_activ':    round(float(prom_actividades), 2) if prom_actividades else None,
                'manual':        float(cal_manual.nota) if cal_manual else None,
                'final':         promedio_final,
            })

        filas.append({'alumno': alumno, 'cols': cols})

    return render(request, 'docente/boleta_grupo.html', {
        'grupo':       grupo,
        'asignaturas': asignaturas,
        'filas':       filas,
    })


@docente_required
def concentrado(request):
    from academic.models import Grupo, Calificacion, EntregaTarea, EntregaActividad
    from users.models import DocenteGrupo
    from django.db.models import Avg

    grupo_id = request.GET.get('grupo_id')
    asignaciones = (
        DocenteGrupo.objects
        .filter(docente=request.user, activo=True)
        .select_related('grupo', 'asignatura')
    )
    grupos = list({a.grupo for a in asignaciones})

    grupo = None
    filas = []
    asignaturas = []

    if grupo_id:
        grupo = get_object_or_404(Grupo, pk=grupo_id)
        asigs_grupo = [a.asignatura for a in asignaciones.filter(grupo=grupo)]
        asignaturas = asigs_grupo
        alumnos = grupo.alumnos.filter(estatus='ACTIVO', rol='ALUMNO').order_by('last_name', 'first_name')

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
                    alumno=alumno, asignatura=asig,
                    grupo=grupo, tipo='MANUAL',
                ).first()

                valores = [v for v in [prom_tareas, prom_activ, cal_manual.nota if cal_manual else None] if v is not None]
                final = round(sum(valores) / len(valores), 2) if valores else None
                cols.append(final)

            valores_fila = [c for c in cols if c is not None]
            promedio_general = round(sum(valores_fila) / len(valores_fila), 2) if valores_fila else None
            filas.append({'alumno': alumno, 'cols': cols, 'promedio_general': promedio_general})

    return render(request, 'docente/concentrado.html', {
        'grupos':      grupos,
        'grupo':       grupo,
        'asignaturas': asignaturas,
        'filas':       filas,
        'grupo_id':    grupo_id,
    })