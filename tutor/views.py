from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from users.models import Tutor, User
from academic.models import (
    Asistencia, EntregaTarea, EntregaActividad,
    Tarea, Actividad, BoletaParcial, Comunicado,
    Calificacion, HorarioClase,
)
from collections import OrderedDict
from django.db import models
from django.http import JsonResponse
from django.template.loader import render_to_string

def _tutor_requerido(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('tutor_id'):
            return redirect('tutor:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def _construir_contexto_dashboard(tutor):
    """Arma el resumen de alumnos + comunicados del tutor. Se usa tanto
    para el render normal como para el endpoint de auto-actualización,
    para no mantener la misma lógica en dos lugares."""
    alumnos = User.objects.filter(
        tutores_asignados__tutor=tutor, rol='ALUMNO'
    ).select_related('alumno_grupo', 'alumno_grupo__carrera').distinct()

    resumen = []
    hoy = timezone.now().date()
    for alumno in alumnos:
        grupo = alumno.alumno_grupo
        mes, anio = hoy.month, hoy.year

        total = Asistencia.objects.filter(alumno=alumno, fecha__month=mes, fecha__year=anio).count()
        pres  = Asistencia.objects.filter(alumno=alumno, fecha__month=mes, fecha__year=anio, estado='P').count()
        pct   = int((pres / total) * 100) if total > 0 else None

        tareas_pendientes = 0
        if grupo:
            tareas_pendientes = Tarea.objects.filter(
                grupo=grupo, publicada=True,
                fecha_entrega__gte=timezone.now()
            ).exclude(entregas__alumno=alumno).count()

        ultima_boleta = BoletaParcial.objects.filter(
            alumno=alumno, publicada=True
        ).order_by('-parcial').first()

        resumen.append({
            'alumno':            alumno,
            'asistencia_pct':    pct,
            'tareas_pendientes': tareas_pendientes,
            'ultima_boleta':     ultima_boleta,
        })

    planteles_ids = {a.alumno_grupo.plantel_id for a in alumnos if a.alumno_grupo}
    grupos_ids    = {a.alumno_grupo_id for a in alumnos if a.alumno_grupo_id}

    comunicados = Comunicado.objects.filter(
        plantel_id__in=planteles_ids,
        activo=True,
        publico__in=['PADRES', 'AMBOS'],
    ).filter(
        models.Q(destinatario='TODOS') |
        models.Q(destinatario='GRUPO', grupo_id__in=grupos_ids)
    ).exclude(
        destinatario='DOCENTES'
    ).select_related('autor', 'grupo').distinct().order_by('-creado_en')[:20]

    return {'resumen': resumen, 'comunicados': comunicados}


def login_tutor(request):
    if request.session.get('tutor_id'):
        return redirect('tutor:dashboard')
    error = None
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        tutor  = Tutor.objects.filter(codigo_acceso=codigo).first()
        if tutor:
            request.session['tutor_id']     = tutor.pk
            request.session['tutor_nombre'] = tutor.nombre
            return redirect('tutor:dashboard')
        error = 'Código incorrecto. Verifica e intenta de nuevo.'
    return render(request, 'tutor/login.html', {'error': error})


def logout_tutor(request):
    request.session.flush()
    return redirect('tutor:login')


@_tutor_requerido
def dashboard_tutor(request):
    tutor = get_object_or_404(Tutor, pk=request.session['tutor_id'])
    contexto = _construir_contexto_dashboard(tutor)
    contexto['tutor'] = tutor
    return render(request, 'tutor/dashboard.html', contexto)


@_tutor_requerido
def dashboard_tutor_actualizar(request):
    """Endpoint JSON: recalcula los datos y devuelve los cards ya
    renderizados en HTML, para que el JS del dashboard los reemplace
    sin recargar la página."""
    tutor = get_object_or_404(Tutor, pk=request.session['tutor_id'])
    contexto = _construir_contexto_dashboard(tutor)
    contexto['tutor'] = tutor

    html_comunicados = render_to_string('tutor/_partials/comunicados_card.html', contexto, request=request)
    html_alumnos = render_to_string('tutor/_partials/alumnos_grid.html', contexto, request=request)

    return JsonResponse({
        'comunicados': html_comunicados,
        'alumnos': html_alumnos,
    })
    

@_tutor_requerido
def perfil_alumno(request, alumno_id):
    tutor = get_object_or_404(Tutor, pk=request.session['tutor_id'])

    alumno = get_object_or_404(
        User.objects.select_related('alumno_grupo', 'alumno_grupo__carrera'),
        pk=alumno_id,
        tutores_asignados__tutor=tutor,
        rol='ALUMNO',
    )
    grupo = alumno.alumno_grupo

    # ── KPIs de asistencia del mes actual ───────────────────────────
    hoy = timezone.now().date()
    asistencias_mes = Asistencia.objects.filter(
        alumno=alumno, fecha__month=hoy.month, fecha__year=hoy.year
    )
    total_mes = asistencias_mes.count()
    pres_mes  = asistencias_mes.filter(estado='P').count()
    ret_mes   = asistencias_mes.filter(estado='R').count()
    aus_mes   = asistencias_mes.filter(estado='A').count()
    pct_mes   = int((pres_mes / total_mes) * 100) if total_mes > 0 else None

    asistencias = Asistencia.objects.filter(
        alumno=alumno
    ).select_related('asignatura').order_by('-fecha')[:30]

    # ── Tareas: TODAS las publicadas del grupo, con estado real de entrega ──
    tareas = []
    if grupo:
        entregas_tarea = {
            e.tarea_id: e for e in EntregaTarea.objects.filter(alumno=alumno)
        }
        for t in Tarea.objects.filter(grupo=grupo, publicada=True).select_related('asignatura').order_by('-fecha_entrega'):
            entrega = entregas_tarea.get(t.id)
            if entrega:
                estado = entrega.estado  # ENTREGADA / CALIFICADA / TARDE
            else:
                estado = 'VENCIDA' if t.vencida else 'PENDIENTE'
            tareas.append({'tarea': t, 'entrega': entrega, 'estado': estado})

    tareas_activas = [x for x in tareas if x['estado'] == 'PENDIENTE']

    # ── Actividades: mismo patrón que tareas ─────────────────────────
    actividades = []
    if grupo:
        entregas_act = {
            e.actividad_id: e for e in EntregaActividad.objects.filter(alumno=alumno)
        }
        for a in Actividad.objects.filter(grupo=grupo, publicada=True).select_related('asignatura').order_by('-fecha_entrega'):
            entrega = entregas_act.get(a.id)
            actividades.append({
                'actividad': a,
                'entrega': entrega,
                'estado': ('CALIFICADA' if entrega and entrega.calificacion is not None
                           else 'ENTREGADA' if entrega
                           else 'VENCIDA' if a.vencida else 'PENDIENTE'),
            })

    # ── Calificaciones sueltas (capturas manuales / de tarea / de actividad), por materia ──
    calificaciones_qs = Calificacion.objects.filter(
        alumno=alumno
    ).select_related('asignatura').order_by('asignatura__nombre', '-fecha')

    calificaciones_por_materia = OrderedDict()
    for c in calificaciones_qs:
        calificaciones_por_materia.setdefault(c.asignatura, []).append(c)

    # ── Boletas finales publicadas, por parcial ──────────────────────
    boletas_qs = BoletaParcial.objects.filter(
        alumno=alumno, publicada=True
    ).select_related('asignatura').order_by('parcial', 'asignatura__nombre')

    boletas_por_parcial = OrderedDict()
    for b in boletas_qs:
        boletas_por_parcial.setdefault(b.parcial, []).append(b)

    # ── Horario de clases del grupo ───────────────────────────────────
    horario = []
    if grupo:
        horario = HorarioClase.objects.filter(
            grupo=grupo, activo=True
        ).select_related('asignatura', 'maestro').order_by('dia', 'hora_inicio')

    # ── Comunicados relevantes ────────────────────────────────────────
    comunicados = []
    if grupo:
        comunicados = Comunicado.objects.filter(
            plantel=grupo.plantel, activo=True, publico__in=['PADRES', 'AMBOS'],
        ).filter(
            models.Q(destinatario='TODOS') | models.Q(destinatario='GRUPO', grupo=grupo)
        ).order_by('-creado_en')[:20]

    return render(request, 'tutor/perfil_alumno.html', {
        'tutor':                      tutor,
        'alumno':                     alumno,
        'grupo':                      grupo,
        'pct_mes':                    pct_mes,
        'pres_mes':                   pres_mes,
        'ret_mes':                    ret_mes,
        'aus_mes':                    aus_mes,
        'asistencias':                asistencias,
        'tareas':                     tareas,
        'tareas_activas':             tareas_activas,
        'actividades':                actividades,
        'calificaciones_por_materia': calificaciones_por_materia,
        'boletas_por_parcial':        boletas_por_parcial,
        'horario':                    horario,
        'comunicados':                comunicados,
    })