from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Avg
import datetime
import json
from django.http import JsonResponse
from .models import Grupo, Periodo, Asignatura, Calificacion, Asistencia, Carrera
from users.models import User, Tutor
from .forms import GrupoForm, AsignaturaForm, AlumnoForm, TutorForm
from users.views import get_campus_theme

def get_plantel_context(user):
    es_uni = user.plantel.id == 2 
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


@login_required
def actualizar_aulas(request):
    if request.method == 'POST':
        plantel = request.user.plantel
        try:
            nuevo_total = int(request.POST.get('total_aulas', 20))
            # Validación: No puedes poner menos aulas de las que ya estás ocupando
            grupos_activos = Grupo.objects.filter(plantel=plantel).count()
            
            if nuevo_total >= grupos_activos:
                plantel.total_aulas = nuevo_total
                plantel.save()
                messages.success(request, f"Capacidad actualizada: {nuevo_total} aulas.")
            else:
                messages.error(request, f"Error: Tienes {grupos_activos} grupos activos. No puedes reducir la capacidad a {nuevo_total}.")
        except ValueError:
            messages.error(request, "Número inválido.")
            
    return redirect('lista_grupos')

@login_required
def lista_grupos(request):
    theme = get_campus_theme(request.user)
    plantel = request.user.plantel
    grupos_base = Grupo.objects.filter(plantel=plantel).prefetch_related('docentes', 'alumnos')

    
    total_aulas = getattr(plantel, 'total_aulas', 20) 
    aulas_ocupadas = grupos_base.count()
    
    if total_aulas > 0:
        porcentaje_ocupacion = int((aulas_ocupadas / total_aulas) * 100)
        disponibles = total_aulas - aulas_ocupadas
    else:
        porcentaje_ocupacion = 100
        disponibles = 0

    info_aulas = {
        'total': total_aulas,
        'ocupadas': aulas_ocupadas,
        'disponibles': disponibles,
        'porcentaje': porcentaje_ocupacion,
        'estado': 'CRÍTICO' if porcentaje_ocupacion >= 90 else 'NORMAL'
    }

    # --- FUNCIÓN PARA CALCULAR KPIs POR NIVEL ---
    def get_kpis(queryset):
        total = queryset.count()
        if total == 0: return {'total': 0, 'promedio': 0.0, 'asistencia': 0, 'alertas': 0}
        
        # 1. Promedio Real
        avg = Calificacion.objects.filter(asignatura__grupo__in=queryset).aggregate(Avg('nota'))['nota__avg']
        promedio = round(avg, 1) if avg else 0.0
        
        # 2. Asistencia Real (Promedio simple)
        asistencias = [g.asistencia_mensual for g in queryset]
        asistencia = round(sum(asistencias) / len(asistencias)) if asistencias else 0
        
        # 3. Alertas (Sin docente o Sobrepoblación)
        alertas = sum(1 for g in queryset if not g.asignaturas.exists() or (g.capacidad_maxima > 0 and g.alumnos.count() >= g.capacidad_maxima))
        
        return {'total': total, 'promedio': promedio, 'asistencia': asistencia, 'alertas': alertas}

    if plantel.id == 2: # Universidad
        carreras_dict = {}
        for g in grupos_base:
            carreras_dict.setdefault(g.carrera, []).append(g)
        return render(request, 'academic/grupos_list_uni.html', {
            'carreras': carreras_dict, 
            'kpis': get_kpis(grupos_base),
            'info_aulas': info_aulas, 
            **theme
        })
    else: # Básica (Separado)
        grupos_sec = grupos_base.filter(carrera__nivel='SECUNDARIA')
        grupos_prepa = grupos_base.filter(carrera__nivel='PREPARATORIA')
        
        return render(request, 'academic/grupos_list_basica.html', {
            'grupos_sec': grupos_sec,
            'grupos_prepa': grupos_prepa,
            'kpis_sec': get_kpis(grupos_sec),
            'kpis_prepa': get_kpis(grupos_prepa),
            'info_aulas': info_aulas,
            **theme
        })
@login_required
def detalle_grupo(request, pk):
    # ─────────────────────────────────────────────
    # Contexto base (colores, labels, etc.)
    # ─────────────────────────────────────────────
    ctx = get_plantel_context(request.user)
    promedio = 0
    asistencia = 0
    alumnos_riesgo = 0

    # ─────────────────────────────────────────────
    # Grupo (blindado por plantel)
    # ─────────────────────────────────────────────
    grupo = get_object_or_404(
        Grupo,
        pk=pk,
        plantel=request.user.plantel
    )

    # ─────────────────────────────────────────────
    # Métricas del grupo
    # ─────────────────────────────────────────────
    promedio = grupo.promedio_general
    asistencia = grupo.asistencia_mensual
    ocupacion = grupo.ocupacion_porcentaje
 # ─────────────────────────────────────────────
    # Alumnos (solo del grupo y plantel)
    # ─────────────────────────────────────────────
   
    alumnos_base = User.objects.filter(
        rol='ALUMNO',
        alumno_grupo=grupo,
        plantel=request.user.plantel
    )

    alumnos_riesgo = alumnos_base.filter(
        notas__nota__lt=6.0
    ).distinct().count()

    query = request.GET.get('q', '')
    alumnos = (
        alumnos_base.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ) if query else alumnos_base
    )

    # ─────────────────────────────────────────────
    # FORMULARIO INSCRIPCIÓN ALUMNO
    # ─────────────────────────────────────────────
    form_alumno = AlumnoForm()

    if request.method == 'POST' and 'btn_inscribir' in request.POST:
        form_alumno = AlumnoForm(request.POST)
        if form_alumno.is_valid():
            form_alumno.save(
                creador=request.user,
                grupo=grupo
            )
            messages.success(request, "Alumno inscrito correctamente.")
            return redirect('detalle_grupo', pk=pk)

    # ─────────────────────────────────────────────
    # FORMULARIO ASIGNAR MATERIA
    # ─────────────────────────────────────────────
    if request.method == 'POST' and 'btn_materia' in request.POST:
        form_mat = AsignaturaForm(request.POST, plantel=request.user.plantel)
        if form_mat.is_valid():
            mat = form_mat.save(commit=False)
            mat.grupo = grupo
            mat.save()
            messages.success(request, "Materia asignada.")
            return redirect('detalle_grupo', pk=pk)
    else:
        form_mat = AsignaturaForm(plantel=request.user.plantel)

    # ─────────────────────────────────────────────
    # Alertas visuales
    # ─────────────────────────────────────────────
    alertas = []
    if not grupo.asignaturas.exists():
        alertas.append("Falta asignar docentes/materias.")
    if grupo.capacidad_maxima > 0 and alumnos_base.count() >= grupo.capacidad_maxima:
        alertas.append("Aula llena.")

    # ─────────────────────────────────────────────
    # Render final
    # ─────────────────────────────────────────────
    return render(request, 'academic/grupo_detail.html', {
        'grupo': grupo,
        'alumnos': alumnos,
        'asignaturas': grupo.asignaturas.all(),
        'form_mat': form_mat,
        'form_alumno': form_alumno,
        'promedio_general': promedio,
        'asistencia_mes': asistencia,
        'alumnos_riesgo': alumnos_riesgo,
        'ocupacion': ocupacion,
        'alertas': alertas,
        'promedio': promedio,
        'asistencia': asistencia,
        'alumnos_riesgo': alumnos_riesgo,
        'query': query,
        **ctx
    })

@login_required
def crear_grupo(request):
    ctx = get_plantel_context(request.user)
    if request.method == 'POST':
        form = GrupoForm(request.POST, plantel=request.user.plantel)
        if form.is_valid():
            g = form.save(commit=False)
            g.plantel = request.user.plantel
            g.save()
            form.save_m2m()
            messages.success(request, "Grupo creado.")
            return redirect('lista_grupos')
    else: form = GrupoForm(plantel=request.user.plantel)
    return render(request, 'academic/grupo_form.html', {'form': form, 'titulo': 'Nuevo Grupo', **ctx})

@login_required
def editar_grupo(request, pk):
    ctx = get_plantel_context(request.user)
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo, plantel=request.user.plantel)
        if form.is_valid():
            form.save()
            messages.success(request, "Grupo actualizado.")
            return redirect('detalle_grupo', pk=pk)
    else: form = GrupoForm(instance=grupo, plantel=request.user.plantel)
    return render(request, 'academic/grupo_form.html', {'form': form, 'titulo': 'Editar Grupo', **ctx})

@login_required
def eliminar_grupo(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
    grupo.delete()
    messages.warning(request, "Grupo eliminado.")
    return redirect('lista_grupos')

@login_required
def promocion_masiva(request):
    if request.user.rol != 'DIRECTOR': return redirect('dashboard')
    if request.method == 'POST':
        plantel = request.user.plantel
        nuevo_periodo_id = request.POST.get('nuevo_periodo')
        Grupo.objects.filter(plantel=plantel).filter(Q(grado=1)|Q(grado=2)).update(
            grado=F('grado')+1, periodo_id=nuevo_periodo_id,
            fecha_inicio=F('fecha_inicio')+datetime.timedelta(days=365),
            fecha_fin=F('fecha_fin')+datetime.timedelta(days=365)
        )
        messages.success(request, "Promoción completada.")
        return redirect('lista_grupos')
    return render(request, 'academic/confirmar_promocion.html', {'periodos': Periodo.objects.filter(activo=True)})

@login_required
def lista_asignaturas(request):
    ctx = get_plantel_context(request.user)
    # FILTRO AUTOMÁTICO DE SEGURIDAD
    plantel_usuario = request.user.plantel
    
    # Solo traigo las carreras DE ESTE PLANTEL
    carreras = Carrera.objects.filter(plantel=plantel_usuario).prefetch_related('asignaturas')
    
    context = {
        'carreras': carreras,
        **ctx,
        'es_universidad': request.user.plantel.id == 2 # Asumo que tienes un campo tipo
    }
    return render(request, 'academic/lista_asignaturas.html', context)
def crear_materia(request):
    plantel = request.user.plantel
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, plantel=plantel)
        if form.is_valid():
            # 1. Obtenemos los datos del formulario
            nombre = form.cleaned_data['nombre']
            clave = form.cleaned_data['clave']
            creditos = form.cleaned_data['creditos']
            grado = form.cleaned_data['grado_destino']
            nivel = form.cleaned_data['nivel_academico']
            docentes_seleccionados = form.cleaned_data['docentes']

            # 2. Buscamos TODOS los grupos que coincidan
            grupos_coincidentes = Grupo.objects.filter(
                plantel=plantel,
                grado=grado,
                carrera__nivel=nivel
            )

            # 3. Creamos la materia para cada grupo
            for grupo in grupos_coincidentes:
                nueva_asignatura = Asignatura.objects.create(
                    grupo=grupo,
                    carrera=grupo.carrera,
                    nombre=nombre,
                    clave=clave,
                    creditos=creditos
                )
                # Asignamos los múltiples docentes
                nueva_asignatura.docentes.set(docentes_seleccionados)

            messages.success(request, f"Materia agregada a {grupos_coincidentes.count()} grupos correctamente.")
            return redirect('lista_asignaturas')
    else:
        form = AsignaturaForm(plantel=plantel)
    
    return render(request, 'academic/materia_form.html', {'form': form})

def alumnos_view(request):
    alumnos = User.objects.filter(rol='ALUMNO')
    alumno_seleccionado = None

    form_tutor = TutorForm()

    if request.method == 'POST' and 'btn_tutor' in request.POST:
        alumno_id = request.POST.get('alumno_id')
        alumno_seleccionado = User.objects.get(id=alumno_id)

        form_tutor = TutorForm(request.POST)
        if form_tutor.is_valid():
            tutor = form_tutor.save(commit=False)
            tutor.alumno = alumno_seleccionado
            tutor.save()

    context = {
        'alumnos': alumnos,
        'alumno': alumno_seleccionado,
        'form_tutor': form_tutor,
    }
    return render(request, 'alumnos.html', context)

@login_required
def agregar_tutor(request):
    if request.method == "POST":
        alumno = get_object_or_404(User, id=request.POST.get("alumno_id"))

        Tutor.objects.create(
            alumno=alumno,
            nombre=request.POST.get("nombre"),
            parentesco=request.POST.get("parentesco"),
            telefono=request.POST.get("telefono"),
            correo=request.POST.get("correo") or None
        )

    return redirect(request.META.get("HTTP_REFERER", "/"))
