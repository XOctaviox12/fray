from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Avg, Count, Case, When, IntegerField
import datetime
import json
from django.http import JsonResponse
from .models import Grupo, Periodo, Asignatura, Calificacion, Asistencia, Carrera, HorarioClase, BoletaParcial
from users.models import User, Tutor
from .forms import GrupoForm, AsignaturaForm, AlumnoForm, TutorForm
from users.views import get_campus_theme
from django.views.generic import DetailView
import random
import string
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from datetime import date as ddate
from datetime import time as dtime
from django.db import transaction

from users.models import DocenteGrupo

from django.contrib.auth import get_user_model
Usuario = get_user_model()
# ─────────────────────────────────────────────────────────────────────────────
# DECORADORES DE ROL
# ─────────────────────────────────────────────────────────────────────────────
ROLES_STAFF = ('DIRECTOR', 'COORDINADOR', 'DOCENTE')
ROLES_ADMIN = ('DIRECTOR', 'COORDINADOR')   # pueden crear/editar horarios


def rol_requerido(*roles):
    """Decorator: redirige al dashboard si el usuario no tiene el rol adecuado."""
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.rol not in roles:
                messages.error(request, "No tienes permiso para acceder a esta sección.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_plantel_context(user):
    plantel = user.plantel
    es_uni = plantel.nivel_educativo == 'SUPERIOR'
    return {
        'color': 'purple' if es_uni else 'blue',
        'hex_color': '#9333ea' if es_uni else '#2563eb',
        'labels': {
            'profesor': 'Catedrático' if es_uni else 'Maestro Tutor',
            'grado_nombre': 'Semestre' if es_uni else 'Grado Escolar',
            'seccion': 'Carrera' if es_uni else 'Sección',
            'dashboard_btn': 'Regresar a Grupos',
        }
    }


def _horarios_plantel_json(plantel):
    """
    Serializa todos los HorarioClase activos del plantel a JSON.
    Se inyecta en el template para verificación de conflictos en el frontend.
    """
    horarios = (
        HorarioClase.objects
        .filter(grupo__plantel=plantel, activo=True)
        .select_related('asignatura', 'maestro', 'grupo')
    )
    data = [
        {
            "id":                h.id,
            "grupo_id":          h.grupo_id,
            "grupo_nombre":      str(h.grupo),
            "maestro_id":        h.maestro_id,
            "maestro_nombre":    h.maestro.get_full_name(),
            "asignatura_id":     h.asignatura_id,
            "asignatura_nombre": h.asignatura.nombre,
            "dia":               h.dia,
            "hora_inicio":       h.hora_inicio.strftime("%H:%M"),
            "hora_fin":          h.hora_fin.strftime("%H:%M"),
            "aula":              h.aula or "",
        }
        for h in horarios
    ]
    return json.dumps(data, ensure_ascii=False)


def _hora_str_a_time(h: str) -> dtime:
    hh, mm = h.split(":")
    return dtime(int(hh), int(mm))


def _extraer_mensaje_ve(ve: ValidationError) -> str:
    """Convierte un ValidationError en un string legible."""
    if hasattr(ve, 'message_dict'):
        partes = []
        for campo, errores in ve.message_dict.items():
            partes.append(f"{campo}: {' '.join(errores)}")
        return " | ".join(partes)
    if hasattr(ve, 'messages'):
        return " ".join(ve.messages)
    return str(ve)


# ─────────────────────────────────────────────────────────────────────────────
# GRUPOS
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def actualizar_aulas(request):
    if request.method == 'POST':
        plantel = request.user.plantel
        try:
            nuevo_total = int(request.POST.get('total_aulas', 20))
            grupos_activos = Grupo.objects.filter(plantel=plantel).count()
            if nuevo_total >= grupos_activos:
                plantel.total_aulas = nuevo_total
                plantel.save()
                messages.success(request, f"Capacidad actualizada: {nuevo_total} aulas.")
            else:
                messages.error(request, f"Tienes {grupos_activos} grupos activos. No puedes reducir a {nuevo_total}.")
        except ValueError:
            messages.error(request, "Número inválido.")
    return redirect('lista_grupos')


@login_required
def lista_grupos(request):
    theme   = get_campus_theme(request.user)
    plantel = request.user.plantel

    periodo_activo = Periodo.objects.filter(plantel=plantel, activo=True).first()

    grupos_base = Grupo.objects.filter(
        plantel=plantel,
        periodo=periodo_activo,          
    ).prefetch_related('docentes', 'alumnos')

    total_aulas        = getattr(plantel, 'total_aulas', 20)
    aulas_ocupadas     = grupos_base.count()
    porcentaje_ocupacion = int((aulas_ocupadas / total_aulas) * 100) if total_aulas > 0 else 100
    disponibles        = max(0, total_aulas - aulas_ocupadas)

    info_aulas = {
        'total':      total_aulas,
        'ocupadas':   aulas_ocupadas,
        'disponibles': disponibles,
        'porcentaje': porcentaje_ocupacion,
        'estado':     'CRÍTICO' if porcentaje_ocupacion >= 90 else 'NORMAL',
    }

    def get_kpis(queryset):
        from django.db.models import Count, Case, When, IntegerField, FloatField
        from django.utils import timezone
        now = timezone.now()

        total = queryset.count()
        if total == 0:
            return {'total': 0, 'promedio': 0.0, 'asistencia': 0, 'alertas': 0}

        # 1 query para promedio de calificaciones
        avg = Calificacion.objects.filter(
            asignatura__grupos__in=queryset
        ).distinct().aggregate(Avg('nota'))['nota__avg']
        promedio = round(avg, 1) if avg else 0.0

        # 1 query para asistencia del mes (en vez de 2 por grupo)
        asistencia_data = Asistencia.objects.filter(
            grupo__in=queryset,
            fecha__month=now.month
        ).aggregate(
            total=Count('id'),
            presentes=Count(Case(When(estado='P', then=1), output_field=IntegerField()))
        )
        if asistencia_data['total']:
            asistencia = int(asistencia_data['presentes'] / asistencia_data['total'] * 100)
        else:
            asistencia = 0

        # 1 query para alertas usando anotaciones
        grupos_con_datos = queryset.annotate(
            num_asignaturas=Count('asignaturas', distinct=True),
            num_alumnos=Count('alumnos', distinct=True)
        )
        alertas = sum(
            1 for g in grupos_con_datos
            if g.num_asignaturas == 0
            or (g.capacidad_maxima > 0 and g.num_alumnos >= g.capacidad_maxima)
        )
        return {'total': total, 'promedio': promedio, 'asistencia': asistencia, 'alertas': alertas}

    if plantel.nivel_educativo == 'SUPERIOR':
        carreras_dict = {}
        for g in grupos_base:
            carreras_dict.setdefault(g.carrera, []).append(g)
        return render(request, 'academic/grupos_list_uni.html', {
            'carreras':   carreras_dict,
            'kpis':       get_kpis(grupos_base),
            'info_aulas': info_aulas,
            **theme
        })
    else:
        grupos_sec   = grupos_base.filter(carrera__nivel='SECUNDARIA')
        grupos_prepa = grupos_base.filter(carrera__nivel='PREPARATORIA')
        return render(request, 'academic/grupos_list_basica.html', {
            'grupos_sec':   grupos_sec,
            'grupos_prepa': grupos_prepa,
            'kpis_sec':     get_kpis(grupos_sec),
            'kpis_prepa':   get_kpis(grupos_prepa),
            'info_aulas':   info_aulas,
            **theme
        })


@login_required
def detalle_grupo(request, pk):
    ctx   = get_plantel_context(request.user)
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
    tiene_acceso = True
    if request.user.rol == 'DOCENTE':
        from users.models import DocenteGrupo
        tiene_acceso = DocenteGrupo.objects.filter(
            docente=request.user, grupo=grupo, activo=True
        ).exists()
    if not tiene_acceso:
        messages.error(request, 'No tienes acceso a este grupo.')
        return redirect('docente_mis_grupos')

    promedio   = grupo.promedio_general
    asistencia = grupo.asistencia_mensual
    ocupacion  = grupo.ocupacion_porcentaje

    alumnos_base   = User.objects.filter(rol='ALUMNO', alumno_grupo=grupo, plantel=request.user.plantel)
    alumnos_riesgo = alumnos_base.filter(notas__nota__lt=6.0).distinct().count()

    query = request.GET.get('q', '')
    alumnos_qs = alumnos_base.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ) if query else alumnos_base

    paginator = Paginator(alumnos_qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    form_alumno = AlumnoForm(request.POST or None)
    if request.method == 'POST' and 'btn_inscribir' in request.POST:
        if form_alumno.is_valid():
            nuevo_alumno, pass_generada = form_alumno.save(creador=request.user, grupo=grupo)
            messages.success(request, f"Inscrito: {nuevo_alumno.username} | Pass temporal: {pass_generada}")
            return redirect('detalle_grupo', pk=pk)

    form_mat = AsignaturaForm(request.POST or None, plantel=request.user.plantel)
    if request.method == 'POST' and 'btn_materia' in request.POST:
        if form_mat.is_valid():
            from users.models import DocenteGrupo
            mat = form_mat.save(commit=False)
            mat.save()
            mat.grupos.add(grupo)
            
            # ── Sincronizar DocenteGrupo automáticamente ──
            docentes_seleccionados = form_mat.cleaned_data.get('docentes', [])
            for docente in docentes_seleccionados:
                mat.docentes.add(docente)
                DocenteGrupo.objects.get_or_create(
                    docente=docente,
                    grupo=grupo,
                    asignatura=mat,
                    defaults={'ciclo': '2026-1', 'activo': True}
                )
            
            messages.success(request, "Materia asignada al grupo.")
            return redirect('detalle_grupo', pk=pk)

    alertas = []
    if not grupo.asignaturas.exists():
        alertas.append("Falta asignar docentes/materias.")
    if grupo.capacidad_maxima > 0 and alumnos_base.count() >= grupo.capacidad_maxima:
        alertas.append("Aula llena.")

    return render(request, 'academic/grupo_detail.html', {
        'grupo':            grupo,
        'alumnos':          page_obj,
        'page_obj':         page_obj,
        'asignaturas':      grupo.asignaturas.all(),
        'form_mat':         form_mat,
        'form_alumno':      form_alumno,
        'promedio_general': promedio,
        'asistencia_mes':   asistencia,
        'alumnos_riesgo':   alumnos_riesgo,
        'ocupacion':        ocupacion,
        'alertas':          alertas,
        'query':            query,
        **ctx
    })


def crear_grupo(request):
    """
    Crear un nuevo grupo académico.
    
    El flujo es:
    1. GET: Mostrar formulario vacío
    2. POST: Validar y guardar
       - GrupoForm valida nivel/grado/especialidad
       - GrupoForm.save() asigna periodo activo automáticamente
       - No hay lógica de periodo en la vista
    """
    ctx = get_plantel_context(request.user)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, plantel=request.user.plantel)
        if form.is_valid():
            try:
                grupo = form.save(commit=False)
                grupo.plantel = request.user.plantel
                # GrupoForm.save() ahora asigna periodo automáticamente
                grupo.save()
                form.save_m2m()  # Guardar docentes (M2M)
                
                messages.success(request, f"✅ Grupo '{grupo}' creado exitosamente.")
                return redirect('lista_grupos')
            
            except Exception as e:
                messages.error(request, f"❌ Error al crear el grupo: {str(e)}")
    else:
        form = GrupoForm(plantel=request.user.plantel)
    
    return render(request, 'academic/grupo_form.html', {
        'form': form,
        'titulo': 'Nuevo Grupo Académico',
        **ctx
    })
 
 
@login_required
def editar_grupo(request, grupo_id):
    ctx = get_plantel_context(request.user)
    """
    Editar un grupo existente.
    
    La especialidad NO se puede cambiar después de creada (regla de negocio).
    """
    grupo = get_object_or_404(Grupo, id=grupo_id, plantel=request.user.plantel)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo, plantel=request.user.plantel)
        if form.is_valid():
            try:
                grupo_actualizado = form.save(commit=False)
                # No permitir cambiar periodo de un grupo existente
                grupo_actualizado.periodo = grupo.periodo
                grupo_actualizado.save()
                form.save_m2m()
                
                messages.success(request, f"✅ Grupo '{grupo}' actualizado.")
                return redirect('lista_grupos')
            
            except Exception as e:
                messages.error(request, f"❌ Error al actualizar: {str(e)}")
    else:
        form = GrupoForm(instance=grupo, plantel=request.user.plantel)
    
    return render(request, 'academic/grupo_form.html', {
        'form': form,
        'titulo': f'Editar Grupo: {grupo}',
        'grupo': grupo,
        **ctx
    })

@login_required
def api_nivel_grado_label(request):
    """
    AJAX: devuelve la etiqueta correcta para el grado según el nivel.
    
    GET /academic/api/nivel-grado-label/?carrera_id=5
    
    Response: {"label": "Semestre / Cuatrimestre"}
    """
    carrera_id = request.GET.get('carrera_id')
    if not carrera_id:
        return JsonResponse({'label': 'Grado Escolar'})
    
    try:
        carrera = Carrera.objects.get(id=carrera_id, plantel=request.user.plantel)
        
        if carrera.nivel in ['PREPARATORIA', 'UNIVERSIDAD']:
            label = 'Semestre / Cuatrimestre'
        else:
            label = 'Grado Escolar'
        
        return JsonResponse({'label': label})
    
    except:
        return JsonResponse({'label': 'Grado Escolar'}, status=400)
 
 
@login_required
def editar_grupo(request, pk):
    ctx   = get_plantel_context(request.user)
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo, plantel=request.user.plantel)
        if form.is_valid():
            form.save()
            messages.success(request, "Grupo actualizado.")
            return redirect('detalle_grupo', pk=pk)
    else:
        form = GrupoForm(instance=grupo, plantel=request.user.plantel)
    return render(request, 'academic/grupo_form.html', {'form': form, 'titulo': 'Editar Grupo', **ctx})


@login_required
def eliminar_grupo(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
    grupo.delete()
    messages.warning(request, "Grupo eliminado.")
    return redirect('lista_grupos')


@login_required
@require_http_methods(["GET", "POST"])
def promocion_masiva(request):
    """Vista de promoción masiva — permitir solo al director."""
    if request.user.rol != 'DIRECTOR':
        return redirect('dashboard')
 
    plantel = request.user.plantel
    if not plantel:
        messages.error(request, 'No tienes plantel asignado.')
        return redirect('dashboard')
 
    periodo_actual = Periodo.objects.filter(plantel=plantel, activo=True).first()
    if not periodo_actual:
        messages.error(request, 'No hay período activo.')
        return redirect('dashboard')
 
    if request.method == 'GET':
        grupos = plantel.grupos.filter(periodo=periodo_actual).order_by('grado')
        pendientes_ids = request.session.get('alumnos_pendientes_especialidad', [])
        context = {
            'grupos': grupos,
            'periodo': periodo_actual,
            'pendientes_count': len(pendientes_ids),
        }
        return render(request, 'academic/promocion_masiva.html', context)
 
    if request.method == 'POST':
        try:
            # ── CAMBIO CRÍTICO: Ejecutar promoción y capturar alumnos pendientes ──
            nuevo_periodo, alumnos_pendientes = periodo_actual.promover_ciclo()
            
            # ── NUEVO: Guardar en sesión para la siguiente vista ──
            request.session['alumnos_pendientes_especialidad'] = [a.id for a in alumnos_pendientes]
            request.session.modified = True
            
            # ── FIN DEL CAMBIO ──
 
            if alumnos_pendientes:
                # Hay alumnos que necesitan asignación de especialidad
                messages.info(
                    request,
                    f'✅ Promoción completada. {len(alumnos_pendientes)} alumno(s) necesitan asignación de especialidad.'
                )
                # Redirigir a la nueva vista de asignación
                return redirect('asignar_especialidades')
            else:
                # Sin pendientes — promoción completada sin necesidad de especialidades
                messages.success(
                    request,
                    f'✅ Promoción completada exitosamente. Nuevo período: {nuevo_periodo.nombre}'
                )
                return redirect('lista_grupos')
 
        except ValidationError as e:
            messages.error(request, f'Error en promoción: {e}')
            return redirect('promocion_masiva')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
            return redirect('promocion_masiva')
 


# ─────────────────────────────────────────────────────────────────────────────
# ASIGNATURAS
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def lista_asignaturas(request):
    ctx      = get_plantel_context(request.user)
    carreras = Carrera.objects.filter(
        plantel=request.user.plantel
    ).prefetch_related('grupos__asignaturas')
    return render(request, 'academic/lista_asignaturas.html', {'carreras': carreras, **ctx})


def _procesar_matriz(request, nueva_asignatura, grupos_destino):
    """Lee la matriz docente-grupo del POST y sincroniza DocenteGrupo."""
    grupo_ids_validos = set(grupos_destino.values_list('id', flat=True))
    pares_raw = request.POST.getlist('matriz_docente_grupo')

    asignaciones = set()
    for par in pares_raw:
        try:
            docente_id_str, grupo_id_str = par.split('_')
            docente_id, grupo_id = int(docente_id_str), int(grupo_id_str)
        except ValueError:
            continue
        if grupo_id not in grupo_ids_validos:
            continue
        asignaciones.add((docente_id, grupo_id))

    docentes_usados_ids = {d for d, _ in asignaciones}
    docentes_map = {
        d.id: d for d in Usuario.objects.filter(id__in=docentes_usados_ids, rol='DOCENTE')
    }
    nueva_asignatura.docentes.set(docentes_map.values())

    # Quitar asignaciones que ya no están marcadas (importante para edición)
    DocenteGrupo.objects.filter(
        asignatura=nueva_asignatura
    ).exclude(
        docente_id__in=docentes_usados_ids
    ).delete()

    pares_existentes = set(
        DocenteGrupo.objects.filter(asignatura=nueva_asignatura)
        .values_list('docente_id', 'grupo_id')
    )
    DocenteGrupo.objects.filter(
        asignatura=nueva_asignatura
    ).exclude(
        docente_id__in=[d for d, g in asignaciones],
        grupo_id__in=[g for d, g in asignaciones]
    ).delete()

    for docente_id, grupo_id in asignaciones:
        if (docente_id, grupo_id) in pares_existentes:
            continue
        docente = docentes_map.get(docente_id)
        if not docente:
            continue
        DocenteGrupo.objects.get_or_create(
            docente=docente,
            grupo_id=grupo_id,
            asignatura=nueva_asignatura,
            defaults={'ciclo': '2026-1', 'activo': True}
        )


@login_required
def crear_materia(request):
    plantel = request.user.plantel
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, plantel=plantel)
        if form.is_valid():
            nombre   = form.cleaned_data['nombre']
            clave    = form.cleaned_data['clave']
            creditos = form.cleaned_data['creditos']
            nivel    = form.cleaned_data['nivel_academico']
            todos    = form.cleaned_data['todos_los_grupos']
            grupos_elegidos = form.cleaned_data['grupos']

            grupos_destino = (
                Grupo.objects.filter(plantel=plantel, carrera__nivel=nivel)
                if todos else grupos_elegidos
            )

            if grupos_destino.exists():
                nueva_asignatura = Asignatura.objects.create(
                    carrera=grupos_destino.first().carrera,
                    nombre=nombre, clave=clave, creditos=creditos
                )
                nueva_asignatura.grupos.set(grupos_destino)
                _procesar_matriz(request, nueva_asignatura, grupos_destino)

                messages.success(
                    request,
                    f"Materia creada y asignada a {grupos_destino.count()} grupo(s)."
                )
            else:
                messages.error(request, f"No se encontraron grupos de nivel {nivel}.")
            return redirect('lista_asignaturas')
    else:
        form = AsignaturaForm(plantel=plantel)
    return render(request, 'academic/materia_form.html', {'form': form})


@login_required
def editar_materia(request, pk):
    plantel = request.user.plantel
    asignatura = get_object_or_404(Asignatura, pk=pk, carrera__plantel=plantel)

    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura, plantel=plantel)
        if form.is_valid():
            nivel = form.cleaned_data['nivel_academico']
            todos = form.cleaned_data['todos_los_grupos']
            grupos_elegidos = form.cleaned_data['grupos']

            grupos_destino = (
                Grupo.objects.filter(plantel=plantel, carrera__nivel=nivel)
                if todos else grupos_elegidos
            )

            if grupos_destino.exists():
                asignatura.nombre = form.cleaned_data['nombre']
                asignatura.clave = form.cleaned_data['clave']
                asignatura.creditos = form.cleaned_data['creditos']
                asignatura.carrera = grupos_destino.first().carrera
                asignatura.save()
                asignatura.grupos.set(grupos_destino)
                _procesar_matriz(request, asignatura, grupos_destino)

                messages.success(request, "Materia actualizada correctamente.")
            else:
                messages.error(request, f"No se encontraron grupos de nivel {nivel}.")
            return redirect('lista_asignaturas')
    else:
        grupos_actuales = asignatura.grupos.all()
        nivel_actual = grupos_actuales.first().carrera.nivel if grupos_actuales.exists() else ''
        form = AsignaturaForm(
            instance=asignatura,
            plantel=plantel,
            initial={
                'nivel_academico': nivel_actual,
                'grupos': grupos_actuales,
                'todos_los_grupos': False,
            }
        )

    matriz_existente = list(
        DocenteGrupo.objects.filter(asignatura=asignatura)
        .values_list('docente_id', 'grupo_id')
    )
    matriz_existente_json = json.dumps([f"{d}_{g}" for d, g in matriz_existente])

    return render(request, 'academic/materia_form.html', {
        'form': form,
        'matriz_existente_json': matriz_existente_json,
    })
# ─────────────────────────────────────────────────────────────────────────────
# ALUMNOS
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def detalle_alumno_json(request, pk):
    alumno = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='ALUMNO')

    tutores = [
        {
            'nombre': t.nombre,
            'parentesco': getattr(t, 'parentesco', ''),
            'telefono': t.telefono,
        }
        for t in alumno.tutores.all()
    ]

    return JsonResponse({
        'nombre': alumno.get_full_name(),
        'username': alumno.username,
        'email': alumno.email or '',
        'telefono': alumno.telefono or '',
        'direccion': alumno.direccion or '',
        'fecha_nacimiento': alumno.fecha_nacimiento.strftime('%d/%m/%Y') if alumno.fecha_nacimiento else '',
        'estatus': alumno.get_estatus_display() if hasattr(alumno, 'get_estatus_display') else 'Activo',
        'activo': alumno.is_active,
        'tutores': tutores,
    })

@login_required
@rol_requerido('DIRECTOR', 'COORD', 'ADMIN')
def alumnos_view(request):
    alumnos = User.objects.filter(rol='ALUMNO', plantel=request.user.plantel)
    alumno_seleccionado = None
    form_tutor         = TutorForm()

    if request.method == 'POST' and 'btn_tutor' in request.POST:
        alumno_seleccionado = get_object_or_404(User, id=request.POST.get('alumno_id'), plantel=request.user.plantel)
        form_tutor = TutorForm(request.POST)
        if form_tutor.is_valid():
            tutor        = form_tutor.save(commit=False)
            tutor.alumno = alumno_seleccionado
            tutor.save()

    return render(request, 'alumnos.html', {
        'alumnos': alumnos,
        'alumno':  alumno_seleccionado,
        'form_tutor': form_tutor,
    })


@login_required
def agregar_tutor(request):
    if request.method == "POST":
        alumno = get_object_or_404(User, id=request.POST.get("alumno_id"), plantel=request.user.plantel)
        Tutor.objects.create(
            alumno=alumno,
            nombre=request.POST.get("nombre"),
            parentesco=request.POST.get("parentesco"),
            telefono=request.POST.get("telefono"),
            correo=request.POST.get("correo") or None,
        )
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def detalle_alumno(request, pk):
    alumno = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='ALUMNO')
    ctx    = get_plantel_context(request.user)
 
    if request.method == 'POST' and request.POST.get('accion') == 'editar':
        alumno.first_name = request.POST.get('first_name', alumno.first_name).strip()
        alumno.last_name  = request.POST.get('last_name',  alumno.last_name).strip()
        alumno.email      = request.POST.get('email',      alumno.email).strip()
        alumno.telefono   = request.POST.get('telefono',   '').strip() or None
        alumno.direccion  = request.POST.get('direccion',  '').strip() or None
        alumno.save()
        messages.success(request, f"Perfil de {alumno.get_full_name()} actualizado.")
        return redirect('detalle_alumno', pk=pk)
 
    # IMPORTANTE: ordenado por periodo (cronológico) y luego por parcial.
    # {% regroup %} en el template NO sirve aquí porque con regroup anidado
    # (periodo -> parcial) el orden se vuelve frágil apenas hay más de un
    # nivel de agrupación; por eso se arma el historial ya agrupado en Python.
    boletas = BoletaParcial.objects.filter(
        alumno=alumno,
        publicada=True
    ).select_related('asignatura', 'grupo', 'grupo__periodo').order_by(
        '-grupo__periodo__fecha_inicio', 'parcial', 'asignatura__nombre'
    )
 
    historial = []
    ciclo_actual = None
    for boleta in boletas:
        periodo = boleta.grupo.periodo
 
        if ciclo_actual is None or ciclo_actual['periodo'].pk != periodo.pk:
            ciclo_actual = {
                'periodo': periodo,
                'grupo': boleta.grupo,
                'parciales': [],
                'notas': [],
            }
            historial.append(ciclo_actual)
 
        parcial_actual = next(
            (p for p in ciclo_actual['parciales'] if p['numero'] == boleta.parcial),
            None,
        )
        if parcial_actual is None:
            parcial_actual = {'numero': boleta.parcial, 'materias': [], 'notas': []}
            ciclo_actual['parciales'].append(parcial_actual)
 
        parcial_actual['materias'].append(boleta)
        parcial_actual['notas'].append(boleta.calificacion_final)
        ciclo_actual['notas'].append(boleta.calificacion_final)
 
    for ciclo in historial:
        ciclo['promedio_ciclo'] = (
            round(sum(ciclo['notas']) / len(ciclo['notas']), 2) if ciclo['notas'] else None
        )
        for p in ciclo['parciales']:
            p['promedio'] = (
                round(sum(p['notas']) / len(p['notas']), 2) if p['notas'] else None
            )
 
    promedio_alumno = boletas.aggregate(Avg('calificacion_final'))['calificacion_final__avg'] or 0.0
 
    asistencias = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')
    total_presentes = asistencias.filter(estado='P').count()
    total_faltas    = asistencias.filter(estado__in=['A', 'R']).count()
    total_registros = asistencias.count()
    porcentaje_asistencia = (
        round((total_presentes / total_registros) * 100) if total_registros > 0 else 0
    )
 
    return render(request, 'academic/alumno_detalle.html', {
        'alumno':                alumno,
        'historial':             historial,           # NUEVO: usar esto en el template
        'calificaciones':        boletas,              # se sigue usando para el resumen general
        'promedio_alumno':       round(promedio_alumno, 1),
        'asistencias':           asistencias,
        'total_presentes':       total_presentes,
        'total_faltas':          total_faltas,
        'porcentaje_asistencia': porcentaje_asistencia,
        **ctx,
    })


@login_required
def editar_alumno(request, pk):
    ctx    = get_plantel_context(request.user)
    alumno = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='ALUMNO')

    from .forms import AlumnoForm
    if request.method == 'POST':
        form = AlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.save()
            messages.success(request, "Datos del alumno actualizados.")
            return redirect('detalle_alumno', pk=pk)
    else:
        form = AlumnoForm(instance=alumno)

    return render(request, 'academic/editar_alumno.html', {'form': form, 'alumno': alumno, **ctx})


@login_required
def regenerar_password(request, pk):
    alumno     = get_object_or_404(User, pk=pk, plantel=request.user.plantel)
    nueva_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    alumno.set_password(nueva_pass)
    alumno.password_plana = nueva_pass  # ← agregar esta línea
    alumno.save()
    messages.success(request, f"Nueva contraseña para {alumno.get_full_name()}: {nueva_pass} — anótala antes de salir.")
    return redirect('detalle_alumno', pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
# ASISTENCIAS
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def pasar_lista(request, grupo_id):
    grupo   = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)
    ctx     = get_plantel_context(request.user)
    hoy     = ddate.today()
    alumnos = User.objects.filter(rol='ALUMNO', alumno_grupo=grupo).order_by('last_name', 'first_name')

    if request.method == 'POST' and 'guardar' in request.POST:
        presentes_ids = set(request.POST.getlist('presentes'))
        
        for alumno in alumnos:
            estado = 'P' if str(alumno.id) in presentes_ids else 'A'
            Asistencia.objects.update_or_create(
                alumno=alumno,
                grupo=grupo,
                asignatura=None,
                fecha=hoy,
                defaults={'estado': estado},
            )

        messages.success(
            request,
            f"Lista del {hoy.strftime('%d/%m/%Y')} guardada — "
            f"{len(presentes_ids)} presentes de {alumnos.count()}."
        )
        return redirect('detalle_grupo', pk=grupo_id)

    # Leer registros existentes
    ya_registrados = {
        a.alumno_id: a.estado
        for a in Asistencia.objects.filter(grupo=grupo, fecha=hoy, asignatura=None)
    }

    return render(request, 'academic/pasar_lista.html', {
        'grupo':          grupo,
        'alumnos':        alumnos,
        'hoy':            hoy,
        'ya_registrados': ya_registrados,
        'primera_vez':    not bool(ya_registrados),
        **ctx,
    })
# ─────────────────────────────────────────────────────────────────────────────
# CALIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def registrar_calificaciones(request, grupo_id, asignatura_id):
    grupo      = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)
    # Fix: verificar que la asignatura pertenece a una carrera del mismo plantel
    asignatura = get_object_or_404(
        Asignatura,
        pk=asignatura_id,
        carrera__plantel=request.user.plantel,   # ← Fix
    )
    ctx     = get_plantel_context(request.user)
    alumnos = User.objects.filter(rol='ALUMNO', alumno_grupo=grupo).order_by('last_name', 'first_name')
    existentes = {
        c.alumno_id: c.nota
        for c in Calificacion.objects.filter(alumno__in=alumnos, asignatura=asignatura)
    }
 
    if request.method == 'POST':
        guardados, errores = 0, []
        for alumno in alumnos:
            raw = request.POST.get(f'nota_{alumno.id}', '').strip()
            if raw == '':
                continue
            try:
                nota = round(max(0.0, min(10.0, float(raw.replace(',', '.')))), 2)
                Calificacion.objects.update_or_create(
                    alumno=alumno, asignatura=asignatura, defaults={'nota': nota}
                )
                guardados += 1
            except ValueError:
                errores.append(alumno.get_full_name())
 
        if guardados:
            messages.success(request, f"{guardados} calificaciones guardadas en {asignatura.nombre}.")
        if errores:
            messages.warning(request, f"Notas inválidas ignoradas: {', '.join(errores)}.")
        return redirect('reporte_calificaciones', grupo_id=grupo_id)
 
    return render(request, 'academic/calificaciones_form.html', {
        'grupo': grupo, 'asignatura': asignatura, 'alumnos': alumnos, 'existentes': existentes, **ctx,
    })

@login_required
def reporte_calificaciones(request, grupo_id):
    grupo       = get_object_or_404(Grupo, pk=grupo_id, plantel=request.user.plantel)
    ctx         = get_plantel_context(request.user)
    alumnos     = User.objects.filter(
        rol='ALUMNO',
        alumno_grupo=grupo,
        plantel=request.user.plantel,            # ← Fix: doble verificación
    ).order_by('last_name', 'first_name')
    asignaturas = grupo.asignaturas.filter(
        carrera__plantel=request.user.plantel    # ← Fix: asignaturas del plantel
    )
 
    tabla = {}
    for alumno in alumnos:
        tabla[alumno.id] = {}
        for asig in asignaturas:
            cal = Calificacion.objects.filter(alumno=alumno, asignatura=asig).first()
            tabla[alumno.id][asig.id] = float(cal.nota) if cal else None
 
    promedios = {}
    for alumno in alumnos:
        notas = [v for v in tabla[alumno.id].values() if v is not None]
        promedios[alumno.id] = round(sum(notas) / len(notas), 1) if notas else None
 
    prom_asig = {}
    for asig in asignaturas:
        notas = [tabla[a.id][asig.id] for a in alumnos if tabla[a.id][asig.id] is not None]
        prom_asig[asig.id] = round(sum(notas) / len(notas), 1) if notas else None
 
    return render(request, 'academic/reporte_calificaciones.html', {
        'grupo': grupo, 'alumnos': alumnos, 'asignaturas': asignaturas,
        'tabla': tabla, 'promedios': promedios, 'prom_asig': prom_asig, **ctx,
    })


## ─────────────────────────────────────────────────────────────────────────────
# HORARIOS — PANEL STAFF (Director / Coordinador / Docente con permiso)
# Alumnos NO tienen acceso a estas vistas. Su app es separada.
# ─────────────────────────────────────────────────────────────────────────────

@rol_requerido('DIRECTOR', 'COORD', 'DOCENTE')
def gestionar_horario_grupo(request, grupo_id):
    grupo   = get_object_or_404(Grupo, id=grupo_id, plantel=request.user.plantel)
    plantel = request.user.plantel

    if request.user.rol == 'DOCENTE' and not grupo.docentes.filter(pk=request.user.pk).exists():
        messages.error(request, "Solo puedes gestionar horarios de los grupos que tienes asignados.")
        return redirect('lista_grupos')

    dias_lista = [
        ('LU', 'Lunes'), ('MA', 'Martes'), ('MI', 'Miércoles'),
        ('JU', 'Jueves'), ('VI', 'Viernes'),
    ]
    horas_lista = [
        "07:00", "08:00", "09:00", "10:00",
        "11:00", "12:00", "13:00", "14:00",
    ]
    dias_opciones = [
        ('LU', 'Lunes'), ('MA', 'Martes'), ('MI', 'Miércoles'),
        ('JU', 'Jueves'), ('VI', 'Viernes'), ('SA', 'Sábado'),
    ]

    horarios_qs = (
        HorarioClase.objects
        .filter(grupo=grupo, activo=True)
        .select_related('asignatura', 'maestro')
    )

    matriz = {}
    for hora in horas_lista:
        t = _hora_str_a_time(hora)
        matriz[hora] = {}
        for dia_code, _ in dias_lista:
            clase = horarios_qs.filter(
                dia=dia_code,
                hora_inicio__hour=t.hour,
                hora_inicio__minute=t.minute,
            ).first()
            matriz[hora][dia_code] = clase

    DIA_HOY_MAP = {0: 'LU', 1: 'MA', 2: 'MI', 3: 'JU', 4: 'VI', 5: 'SA', 6: 'SA'}
    dia_hoy = DIA_HOY_MAP.get(datetime.date.today().weekday(), '')

    if request.user.rol in ('DIRECTOR', 'COORD'):
        maestros = User.objects.filter(plantel=plantel, rol='DOCENTE').order_by('first_name')
    else:
        maestros = User.objects.filter(pk=request.user.pk)

    asignaturas = Asignatura.objects.filter(carrera__plantel=plantel).distinct()

    return render(request, 'academic/gestionar_horario.html', {
        'grupo':         grupo,
        'dias_lista':    dias_lista,
        'dias_opciones': dias_opciones,
        'horas_lista':   horas_lista,
        'matriz':        matriz,
        'dia_hoy':       dia_hoy,
        'asignaturas':   asignaturas,
        'maestros':      maestros,
        'puede_editar':  request.user.rol in ('DIRECTOR', 'COORD'),
        'horarios_json': _horarios_plantel_json(plantel),
        'rol':           request.user.rol,
    })


@rol_requerido('DIRECTOR', 'COORD')
def crear_clase(request):
    plantel_usuario = request.user.plantel
    theme           = get_campus_theme(request.user)
    grupo_id        = request.GET.get('grupo') or request.POST.get('grupo')

    if request.method == 'POST':
        asignatura_id      = request.POST.get('asignatura')
        maestro_id         = request.POST.get('maestro')
        dias_seleccionados = request.POST.getlist('dias')
        hora_inicio        = request.POST.get('hora_inicio')
        hora_fin           = request.POST.get('hora_fin')
        aula               = request.POST.get('aula', '').strip() or 'Por definir'
        grupo_id_post      = request.POST.get('grupo')

        errors = []
        if not grupo_id_post:      errors.append("Debes seleccionar un grupo.")
        if not asignatura_id:      errors.append("Debes seleccionar una asignatura.")
        if not maestro_id:         errors.append("Debes seleccionar un docente.")
        if not dias_seleccionados: errors.append("Selecciona al menos un día.")
        if not hora_inicio:        errors.append("La hora de inicio es obligatoria.")
        if not hora_fin:           errors.append("La hora de fin es obligatoria.")
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            errors.append("La hora de fin debe ser posterior a la de inicio.")

        for err in errors:
            messages.error(request, err)

        if not errors:
            try:
                grupo      = get_object_or_404(Grupo,      id=grupo_id_post, plantel=plantel_usuario)
                asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                maestro    = get_object_or_404(User,       id=maestro_id)

                creados, errores_ve = 0, []
                for dia_code in dias_seleccionados:
                    try:
                        HorarioClase.objects.create(
                            grupo=grupo, asignatura=asignatura, maestro=maestro,
                            dia=dia_code, hora_inicio=hora_inicio, hora_fin=hora_fin, aula=aula,
                        )
                        creados += 1
                    except ValidationError as ve:
                        errores_ve.append(_extraer_mensaje_ve(ve))

                if creados:
                    messages.success(request, f"✅ {creados} bloque(s) guardados para {grupo.nombre}.")
                for err in errores_ve:
                    messages.error(request, f"⚠️ {err}")
                if creados:
                    return redirect('gestionar_horario', grupo_id=grupo.id)

            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

    grupo_seleccionado = None
    if grupo_id:
        grupo_seleccionado = Grupo.objects.filter(id=grupo_id, plantel=plantel_usuario).first()

    return render(request, 'academic/form_clase.html', {
        'grupo_seleccionado': grupo_seleccionado,
        'grupos':             Grupo.objects.filter(plantel=plantel_usuario).order_by('grado', 'nombre'),
        'asignaturas':        Asignatura.objects.filter(carrera__plantel=plantel_usuario).distinct(),
        'maestros':           User.objects.filter(plantel=plantel_usuario, rol='DOCENTE').order_by('first_name'),
        'dia_preselect':      request.GET.get('dia', ''),
        'hora_preselect':     request.GET.get('hora', ''),
        'dias_opciones': [
            ('LU', 'Lunes'), ('MA', 'Martes'), ('MI', 'Miércoles'),
            ('JU', 'Jueves'), ('VI', 'Viernes'), ('SA', 'Sábado'),
        ],
        'horarios_json': _horarios_plantel_json(plantel_usuario),
        **theme
    })


@rol_requerido('DIRECTOR', 'COORD')
def editar_clase(request, clase_id):
    plantel = request.user.plantel
    clase   = get_object_or_404(HorarioClase, id=clase_id, grupo__plantel=plantel)

    if request.method != 'POST':
        return redirect('gestionar_horario', grupo_id=clase.grupo_id)

    asignatura_id = request.POST.get('asignatura')
    maestro_id    = request.POST.get('maestro')
    dias_list     = request.POST.getlist('dias')
    dia           = dias_list[0] if dias_list else request.POST.get('dias', '')
    hora_inicio   = request.POST.get('hora_inicio')
    hora_fin      = request.POST.get('hora_fin')
    aula          = request.POST.get('aula', '').strip() or 'Por definir'

    errors = []
    if not asignatura_id: errors.append("Debes seleccionar una asignatura.")
    if not maestro_id:    errors.append("Debes seleccionar un docente.")
    if not dia:           errors.append("Debes seleccionar el día.")
    if not hora_inicio:   errors.append("La hora de inicio es obligatoria.")
    if not hora_fin:      errors.append("La hora de fin es obligatoria.")
    if hora_inicio and hora_fin and hora_inicio >= hora_fin:
        errors.append("La hora de fin debe ser posterior a la de inicio.")

    for err in errors:
        messages.error(request, err)

    if not errors:
        try:
            asignatura = get_object_or_404(Asignatura, id=asignatura_id)
            maestro    = get_object_or_404(User, id=maestro_id, plantel=plantel, rol='DOCENTE')

            clase.asignatura  = asignatura
            clase.maestro     = maestro
            clase.dia         = dia
            clase.hora_inicio = hora_inicio
            clase.hora_fin    = hora_fin
            clase.aula        = aula
            clase.full_clean()
            clase.save()

            messages.success(request, f"✅ Clase '{asignatura.nombre}' actualizada.")
            return redirect('gestionar_horario', grupo_id=clase.grupo_id)

        except ValidationError as ve:
            messages.error(request, f"⚠️ {_extraer_mensaje_ve(ve)}")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")

    return redirect('gestionar_horario', grupo_id=clase.grupo_id)


@rol_requerido('DIRECTOR', 'COORD')
def eliminar_clase(request, clase_id):
    clase = get_object_or_404(HorarioClase, id=clase_id, grupo__plantel=request.user.plantel)

    if request.method == 'POST':
        grupo_id = clase.grupo_id
        nombre   = clase.asignatura.nombre
        clase.delete()
        messages.success(request, f"Clase '{nombre}' eliminada.")
        return redirect('gestionar_horario', grupo_id=grupo_id)

    return redirect('gestionar_horario', grupo_id=clase.grupo_id)


# ─────────────────────────────────────────────────────────────────────────────
# HORARIOS — VISTA ALUMNO (solo lectura)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def carga_horaria_alumno(request):
    rol     = request.user.rol
    plantel = request.user.plantel
    theme   = get_campus_theme(request.user)

    # ── Director y Coordinador: lista de grupos separada por nivel ──
    if rol in ('DIRECTOR', 'COORD'):
        grupos_base  = (
            Grupo.objects
            .filter(plantel=plantel)
            .order_by('grado', 'nombre')
            .select_related('carrera')
            .prefetch_related('alumnos', 'docentes')
        )
        grupos_sec   = grupos_base.filter(carrera__nivel='SECUNDARIA')
        grupos_prepa = grupos_base.filter(carrera__nivel='PREPARATORIA')

        return render(request, 'academic/carga_horaria.html', {
            'grupos_sec':   grupos_sec,
            'grupos_prepa': grupos_prepa,
            **theme,
        })

    # ── Docente: sus grupos asignados ──
    if rol == 'DOCENTE':
        grupos_base  = (
            Grupo.objects
            .filter(plantel=plantel, docentes=request.user)
            .order_by('grado', 'nombre')
            .select_related('carrera')
            .prefetch_related('alumnos', 'docentes')
        )
        grupos_sec   = grupos_base.filter(carrera__nivel='SECUNDARIA')
        grupos_prepa = grupos_base.filter(carrera__nivel='PREPARATORIA')

        return render(request, 'academic/horario_docente.html', {
            'grupos_sec':   grupos_sec,
            'grupos_prepa': grupos_prepa,
            'titulo':       'Mis grupos asignados',
            **theme,
        })

    # ── Alumno: solo lectura de su propio horario ──
    grupo = getattr(request.user, 'alumno_grupo', None)
    if grupo:
        horarios = (
            HorarioClase.objects
            .filter(grupo=grupo, activo=True)
            .select_related('asignatura', 'maestro')
            .order_by('dia', 'hora_inicio')
        )
    else:
        horarios = HorarioClase.objects.none()
        messages.info(request, "Aún no tienes un grupo asignado.")

    return render(request, 'academic/carga_horaria.html', {
        'alumno':   request.user,
        'horarios': horarios,
        'color':    'indigo',
        **theme,
    })

# ─────────────────────────────────────────────────────────────────────────────
# API AJAX: verificar conflicto (backup server-side)
# ─────────────────────────────────────────────────────────────────────────────

@rol_requerido('DIRECTOR', 'COORD')
def api_verificar_conflicto(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'conflictos': ['Método no permitido.']})

    try:
        data       = json.loads(request.body)
        maestro_id = data.get('maestro_id')
        grupo_id   = data.get('grupo_id')
        aula       = data.get('aula', '').strip()
        dia        = data.get('dia')
        hora_ini   = data.get('hora_inicio')
        hora_fin   = data.get('hora_fin')
        excluir_id = data.get('excluir_id')

        if not all([dia, hora_ini, hora_fin]):
            return JsonResponse({'ok': True, 'conflictos': []})

        qs = HorarioClase.objects.filter(
            dia=dia, activo=True,
            hora_inicio__lt=hora_fin, hora_fin__gt=hora_ini,
            grupo__plantel=request.user.plantel,
        )
        if excluir_id:
            qs = qs.exclude(pk=excluir_id)

        conflictos = []
        if maestro_id:
            conf = qs.filter(maestro_id=maestro_id).select_related('asignatura').first()
            if conf:
                conflictos.append(
                    f"El docente ya tiene '{conf.asignatura.nombre}' "
                    f"los {conf.get_dia_display()} {conf.hora_inicio:%H:%M}–{conf.hora_fin:%H:%M}."
                )
        if grupo_id:
            conf = qs.filter(grupo_id=grupo_id).select_related('asignatura').first()
            if conf:
                conflictos.append(
                    f"El grupo ya tiene '{conf.asignatura.nombre}' "
                    f"los {conf.get_dia_display()} {conf.hora_inicio:%H:%M}–{conf.hora_fin:%H:%M}."
                )
        if aula and aula != 'Por definir':
            conf = qs.filter(aula=aula).select_related('asignatura').first()
            if conf:
                conflictos.append(
                    f"El aula '{aula}' está ocupada con '{conf.asignatura.nombre}' "
                    f"{conf.hora_inicio:%H:%M}–{conf.hora_fin:%H:%M}."
                )

        return JsonResponse({'ok': len(conflictos) == 0, 'conflictos': conflictos})

    except Exception as e:
        return JsonResponse({'ok': False, 'conflictos': [str(e)]})
    
@login_required
def lista_horarios_pdf(request):
    from academic.models import HorarioPDF, Grupo
    plantel = request.user.plantel

    grupos = Grupo.objects.filter(plantel=plantel).order_by('grado', 'nombre')
    horarios = {h.grupo_id: h for h in HorarioPDF.objects.filter(plantel=plantel).select_related('grupo', 'subido_por')}

    filas = []
    for grupo in grupos:
        filas.append({
            'grupo':   grupo,
            'horario': horarios.get(grupo.pk),
        })

    return render(request, 'academic/horarios_pdf.html', {
        'filas': filas,
    })


@login_required
def subir_horario_pdf(request):
    from academic.models import HorarioPDF, Grupo
    plantel = request.user.plantel
    grupos  = Grupo.objects.filter(plantel=plantel).order_by('grado', 'nombre')

    if request.method == 'POST':
        grupo_id = request.POST.get('grupo_id')
        archivo  = request.FILES.get('archivo')

        if not grupo_id or not archivo:
            messages.error(request, 'Selecciona un grupo y un archivo PDF.')
        else:
            grupo = get_object_or_404(Grupo, pk=grupo_id, plantel=plantel)
            HorarioPDF.objects.update_or_create(
                grupo=grupo,
                defaults={
                    'plantel':    plantel,
                    'archivo':    archivo,
                    'subido_por': request.user,
                }
            )
            messages.success(request, f'Horario de {grupo} subido correctamente.')
            return redirect('lista_horarios_pdf')

    return render(request, 'academic/subir_horario_pdf.html', {
        'grupos': grupos,
    })


@login_required
def eliminar_horario_pdf(request, pk):
    from academic.models import HorarioPDF
    horario = get_object_or_404(HorarioPDF, pk=pk, plantel=request.user.plantel)
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado.')
    return redirect('lista_horarios_pdf')


@login_required
@require_http_methods(["GET", "POST"])
def asignar_especialidades(request):
    """
    Vista para asignar especialidades a alumnos que pasan de 4° a 5° en Preparatoria.

    GET: Muestra formulario con lista de alumnos pendientes (desde sesión o BD)
    POST: Procesa las asignaciones y mueve alumnos a grupos de 5°

    Flujo híbrido: permite asignar uno por uno O por lotes.
    Crea automáticamente grupos de 5° si no existen.
    """

    # Solo Director
    if request.user.rol != 'DIRECTOR':
        messages.error(request, 'Solo directores pueden asignar especialidades.')
        return redirect('dashboard')

    plantel = request.user.plantel
    if not plantel:
        messages.error(request, 'No tienes plantel asignado.')
        return redirect('dashboard')

    # Obtener periodo activo
    periodo_activo = Periodo.objects.filter(plantel=plantel, activo=True).first()
    if not periodo_activo:
        messages.error(request, 'No hay período activo en tu plantel.')
        return redirect('dashboard')

    # Recuperar alumnos pendientes (desde sesión o BD)
    alumnos_pendientes_ids = request.session.get('alumnos_pendientes_especialidad', [])

    if not alumnos_pendientes_ids:
        alumnos_pendientes = User.objects.filter(
            rol='ALUMNO',
            plantel=plantel,
            alumno_grupo__isnull=True,
        ).distinct().order_by('last_name', 'first_name')
    else:
        alumnos_pendientes = User.objects.filter(id__in=alumnos_pendientes_ids)

    if not alumnos_pendientes.exists():
        messages.info(request, 'No hay alumnos pendientes de asignación de especialidad.')
        return redirect('promocion_masiva')

    especialidades = Grupo.ESPECIALIDADES

    if request.method == 'GET':
        alumnos_data = []
        for alumno in alumnos_pendientes:
            alumnos_data.append({
                'id': alumno.id,
                'nombre': alumno.get_full_name() or alumno.username,
                'username': alumno.username,
            })

        context = {
            'alumnos': alumnos_data,
            'especialidades': especialidades,
            'total_pendientes': len(alumnos_data),
            'periodo': periodo_activo,
        }
        return render(request, 'academic/asignar_especialidades.html', context)

    # POST: Procesar asignaciones
    if request.method == 'POST':
        asignaciones = request.POST.getlist('asignaciones')  # Lista de "alumno_id:especialidad"

        if not asignaciones:
            messages.error(request, 'Debes seleccionar al menos una asignación.')
            return redirect('asignar_especialidades')

        # CAMBIO 3: bloquear alumno con más de una especialidad ANTES de procesar nada
        alumno_ids_vistos = set()
        for item in asignaciones:
            aid = item.split(':')[0]
            if aid in alumno_ids_vistos:
                messages.error(request, f'El alumno {aid} tiene más de una especialidad seleccionada.')
                return redirect('asignar_especialidades')
            alumno_ids_vistos.add(aid)
        # FIN CAMBIO 3

        try:
            with transaction.atomic():
                resultados = {
                    'exitosas': 0,
                    'errores': [],
                }

                for item in asignaciones:
                    alumno_id = item  # valor de respaldo para el reporte de error
                    try:
                        with transaction.atomic():  # CAMBIO 4: savepoint individual por alumno
                            alumno_id, especialidad = item.split(':')
                            alumno = User.objects.get(id=int(alumno_id), rol='ALUMNO')

                            esp_dict = dict(Grupo.ESPECIALIDADES)
                            if especialidad not in esp_dict:
                                raise ValueError(f'Especialidad inválida: {especialidad}')

                            carrera = Carrera.objects.filter(
                                plantel=plantel,
                                nivel='PREPARATORIA',
                            ).first()

                            if not carrera:
                                raise ValueError('No existe carrera de Preparatoria en tu plantel.')

                            grupo_5to, creado = Grupo.objects.get_or_create(
                                plantel=plantel,
                                periodo=periodo_activo,
                                carrera=carrera,
                                grado=5,
                                especialidad=especialidad,
                                defaults={
                                    'aula': f'Aula 5° - {esp_dict[especialidad]}',
                                    'capacidad_maxima': 30,
                                }
                            )

                            alumno.alumno_grupo = grupo_5to
                            alumno.save(update_fields=['alumno_grupo'])

                            resultados['exitosas'] += 1
                        # FIN CAMBIO 4 — este except cierra el 'with' interno, no el for

                    except (User.DoesNotExist, ValueError, Carrera.DoesNotExist) as e:
                        resultados['errores'].append({'alumno_id': alumno_id, 'mensaje': str(e)})

                # Limpiar sesión
                if 'alumnos_pendientes_especialidad' in request.session:
                    del request.session['alumnos_pendientes_especialidad']

                # Mensaje resumen
                msg = f'✅ {resultados["exitosas"]} alumno(s) asignado(s) exitosamente.'
                if resultados['errores']:
                    msg += f' ⚠️ {len(resultados["errores"])} error(es).'
                messages.success(request, msg)

                return redirect('promocion_masiva')

        except Exception as e:
            messages.error(request, f'Error al procesar asignaciones: {str(e)}')
            return redirect('asignar_especialidades')
 
@login_required
@require_http_methods(["GET"])
def api_grupos_especialidad(request):
    """
    API AJAX: devuelve lista de grupos de 5° para una especialidad elegida.
    GET params: especialidad (clave), para que el frontend pueda mostrar
    el grupo actual o el que se va a crear.
    """
    especialidad = request.GET.get('especialidad', '')

    # CAMBIO: respuesta JSON en vez de messages+redirect (esto es un endpoint AJAX)
    if request.user.rol != 'DIRECTOR':
        return JsonResponse({'error': 'No autorizado'}, status=403)

    plantel = request.user.plantel
    if not plantel:
        return JsonResponse({'error': 'No tienes plantel asignado'}, status=400)

    periodo_activo = Periodo.objects.filter(plantel=plantel, activo=True).first()

    if not periodo_activo:
        return JsonResponse({'error': 'No hay período activo'}, status=400)

    # Buscar grupo de 5° con esa especialidad
    grupo = Grupo.objects.filter(
        plantel=plantel,
        periodo=periodo_activo,
        grado=5,
        especialidad=especialidad,
    ).first()

    esp_dict = dict(Grupo.ESPECIALIDADES)
    esp_label = esp_dict.get(especialidad, 'Desconocida')

    return JsonResponse({
        'especialidad': especialidad,
        'label': esp_label,
        'grupo_existe': grupo is not None,
        'grupo': {
            'id': grupo.id,
            'nombre': grupo.nombre,
            'ocupacion': grupo.ocupacion_porcentaje,
            'alumnos': grupo.alumnos.count(),
        } if grupo else None,
    })

@login_required
@require_http_methods(["POST"])
def crear_periodo(request):
    """Alta manual de un período — usado desde el panel de promoción
    masiva para configurar el primer período de un plantel nuevo, o
    para registrar un período fuera del flujo automático de promoción."""
    if request.user.rol != 'DIRECTOR':
        messages.error(request, 'Solo el Director puede dar de alta un período.')
        return redirect('promocion_masiva')

    plantel = request.user.plantel

    nombre       = request.POST.get('nombre', '').strip()
    tipo         = request.POST.get('tipo', '').strip()
    fecha_inicio = request.POST.get('fecha_inicio', '').strip()
    fecha_fin    = request.POST.get('fecha_fin', '').strip()
    activar      = request.POST.get('activar') == 'on'

    if not nombre or not tipo or not fecha_inicio or not fecha_fin:
        messages.error(request, 'Todos los campos son obligatorios.')
        return redirect('promocion_masiva')

    if tipo not in ('NON', 'PAR'):
        messages.error(request, 'Tipo de período inválido.')
        return redirect('promocion_masiva')

    try:
        with transaction.atomic():
            if activar:
                # Solo puede existir un período activo por plantel
                # (constraint uq_periodo_un_activo_por_plantel), así
                # que desactivamos el actual antes de crear el nuevo.
                Periodo.objects.filter(plantel=plantel, activo=True).update(activo=False)

            nuevo_periodo = Periodo.objects.create(
                nombre=nombre,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                activo=activar,
                plantel=plantel,
            )

        logger.info(f"[crear_periodo] Período '{nombre}' creado por {request.user} (plantel {plantel.id}, activo={activar})")
        messages.success(request, f'✅ Período "{nombre}" creado correctamente.')

    except Exception as e:
        logger.exception(f"[crear_periodo] Error al crear período: {e}")
        messages.error(request, f'Ocurrió un error al crear el período: {e}')

    return redirect('promocion_masiva')

@login_required
def historial_academico_alumno(request, pk):
    """
    Historial académico completo de un alumno: calificaciones finales
    por parcial (BoletaParcial, ya publicadas), agrupadas por ciclo
    (periodo) y por parcial dentro de cada ciclo.
 
    Pensado principalmente para consultar el historial de alumnos ya
    graduados (desde la sección Graduados), pero funciona para
    cualquier alumno del plantel.
    """
    if request.user.rol not in ('DIRECTOR', 'COORD', 'ADMIN'):
        messages.error(request, 'No tienes permiso para ver esta sección.')
        return redirect('dashboard')
 
    alumno = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='ALUMNO')
 
    boletas = BoletaParcial.objects.filter(
        alumno=alumno, publicada=True
    ).select_related('asignatura', 'grupo', 'grupo__periodo').order_by(
        '-grupo__periodo__fecha_inicio', 'parcial', 'asignatura__nombre'
    )
 
    from itertools import groupby
 
    ciclos = []
    for periodo, boletas_periodo in groupby(boletas, key=lambda b: b.grupo.periodo):
        boletas_periodo = list(boletas_periodo)
        grupo_del_ciclo = boletas_periodo[0].grupo
 
        # Agrupar por número de parcial dentro de este ciclo
        parciales_dict = {}
        for b in boletas_periodo:
            parciales_dict.setdefault(b.parcial, []).append(b)
 
        parciales_lista = []
        for num_parcial in sorted(parciales_dict.keys()):
            materias = parciales_dict[num_parcial]
            notas = [float(b.calificacion_final) for b in materias]
            promedio_parcial = round(sum(notas) / len(notas), 2) if notas else None
            parciales_lista.append({
                'numero': num_parcial,
                'materias': materias,
                'promedio': promedio_parcial,
            })
 
        notas_ciclo = [float(b.calificacion_final) for b in boletas_periodo]
        promedio_ciclo = round(sum(notas_ciclo) / len(notas_ciclo), 2) if notas_ciclo else None
 
        ciclos.append({
            'periodo': periodo,
            'grupo': grupo_del_ciclo,
            'parciales': parciales_lista,
            'promedio_ciclo': promedio_ciclo,
        })
 
    return render(request, 'academic/historial_academico.html', {
        'alumno': alumno,
        'ciclos': ciclos,
    })
 