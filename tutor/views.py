from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from users.models import Tutor, User
from academic.models import (
    Asistencia, EntregaTarea, EntregaActividad,
    Tarea, Actividad, BoletaParcial
)


def _tutor_requerido(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('tutor_id'):
            return redirect('tutor:login')
        return view_func(request, *args, **kwargs)
    return wrapper


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
    tutor   = get_object_or_404(Tutor, pk=request.session['tutor_id'])
    alumnos = User.objects.filter(
        tutores=tutor, rol='ALUMNO'
    ).select_related('alumno_grupo', 'alumno_grupo__carrera')

    resumen = []
    hoy     = timezone.now().date()
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

        # Última boleta publicada
        ultima_boleta = BoletaParcial.objects.filter(
            alumno=alumno, publicada=True
        ).order_by('-parcial').first()

        resumen.append({
            'alumno':            alumno,
            'asistencia_pct':    pct,
            'tareas_pendientes': tareas_pendientes,
            'ultima_boleta':     ultima_boleta,
        })

    return render(request, 'tutor/dashboard.html', {
        'tutor':   tutor,
        'resumen': resumen,
    })


@_tutor_requerido
def perfil_alumno(request, pk):
    tutor  = get_object_or_404(Tutor, pk=request.session['tutor_id'])
    alumno = get_object_or_404(User, pk=pk, rol='ALUMNO', tutores=tutor)
    grupo  = alumno.alumno_grupo
    hoy    = timezone.now().date()
    mes, anio = hoy.month, hoy.year

    # Asistencia
    asistencias_qs = Asistencia.objects.filter(alumno=alumno)
    total_mes = asistencias_qs.filter(fecha__month=mes, fecha__year=anio).count()
    pres_mes  = asistencias_qs.filter(fecha__month=mes, fecha__year=anio, estado='P').count()
    ret_mes   = asistencias_qs.filter(fecha__month=mes, fecha__year=anio, estado='R').count()
    aus_mes   = asistencias_qs.filter(fecha__month=mes, fecha__year=anio, estado='A').count()
    pct_mes   = int((pres_mes / total_mes) * 100) if total_mes > 0 else None

    # Boletas parciales publicadas — agrupadas por parcial
    boletas_qs = BoletaParcial.objects.filter(
        alumno=alumno, publicada=True
    ).select_related('asignatura').order_by('parcial', 'asignatura__nombre')

    boletas_por_parcial = {}
    for b in boletas_qs:
        boletas_por_parcial.setdefault(b.parcial, []).append(b)

    # Tareas pendientes
    tareas_activas = []
    if grupo:
        tareas_activas = Tarea.objects.filter(
            grupo=grupo, publicada=True,
            fecha_entrega__gte=timezone.now(),
        ).exclude(entregas__alumno=alumno).order_by('fecha_entrega')

    # Comunicados
    comunicados = []
    if grupo:
        from academic.models import Comunicado
        try:
            comunicados = Comunicado.objects.filter(grupo=grupo).order_by('-creado_en')[:10]
        except Exception:
            comunicados = []

    return render(request, 'tutor/perfil_alumno.html', {
        'tutor':               tutor,
        'alumno':              alumno,
        'grupo':               grupo,
        'asistencias':         asistencias_qs.order_by('-fecha')[:30],
        'total_mes':           total_mes,
        'pres_mes':            pres_mes,
        'ret_mes':             ret_mes,
        'aus_mes':             aus_mes,
        'pct_mes':             pct_mes,
        'boletas_por_parcial': boletas_por_parcial,
        'tareas_activas':      tareas_activas,
        'comunicados':         comunicados,
        'hoy':                 hoy,
    })