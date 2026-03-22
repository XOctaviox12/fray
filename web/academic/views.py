from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Avg
import datetime
import json
from django.http import JsonResponse
from .models import Grupo, Periodo, Asignatura, Calificacion, Asistencia, Carrera, HorarioClase
from users.models import User, Tutor
from .forms import GrupoForm, AsignaturaForm, AlumnoForm, TutorForm
from users.views import get_campus_theme
from django.views.generic import DetailView
import random
import string
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

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
    # Prefetch optimizado para ManyToMany
    grupos_base = Grupo.objects.filter(plantel=plantel).prefetch_related('docentes', 'alumnos')

    total_aulas = getattr(plantel, 'total_aulas', 20) 
    aulas_ocupadas = grupos_base.count()
    
    porcentaje_ocupacion = int((aulas_ocupadas / total_aulas) * 100) if total_aulas > 0 else 100
    disponibles = max(0, total_aulas - aulas_ocupadas)

    info_aulas = {
        'total': total_aulas,
        'ocupadas': aulas_ocupadas,
        'disponibles': disponibles,
        'porcentaje': porcentaje_ocupacion,
        'estado': 'CRÍTICO' if porcentaje_ocupacion >= 90 else 'NORMAL'
    }

    def get_kpis(queryset):
        total = queryset.count()
        if total == 0: return {'total': 0, 'promedio': 0.0, 'asistencia': 0, 'alertas': 0}
        
        # 1. Promedio Real (Usando 'grupos' en plural y distinct)
        avg = Calificacion.objects.filter(
            asignatura__grupos__in=queryset
        ).distinct().aggregate(Avg('nota'))['nota__avg']
        
        promedio = round(avg, 1) if avg else 0.0
        
        # 2. Asistencia Real
        asistencias = [g.asistencia_mensual for g in queryset]
        asistencia = round(sum(asistencias) / len(asistencias)) if asistencias else 0
        
        # 3. Alertas (Basado en la relación inversa de asignatura_set o el related_name)
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
    else: # Básica
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
    ctx   = get_plantel_context(request.user)
    grupo = get_object_or_404(Grupo, pk=pk, plantel=request.user.plantel)
 
    promedio   = grupo.promedio_general
    asistencia = grupo.asistencia_mensual
    ocupacion  = grupo.ocupacion_porcentaje
 
    alumnos_base = User.objects.filter(
        rol='ALUMNO', alumno_grupo=grupo, plantel=request.user.plantel
    )
    alumnos_riesgo = alumnos_base.filter(notas__nota__lt=6.0).distinct().count()
 
    query = request.GET.get('q', '')
    if query:
        alumnos_qs = alumnos_base.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    else:
        alumnos_qs = alumnos_base
 
    # ── Paginación: 20 alumnos por página ────────────────────────────
    paginator  = Paginator(alumnos_qs, 20)
    page_num   = request.GET.get('page', 1)
    page_obj   = paginator.get_page(page_num)
 
    # ── Formulario Alumno ─────────────────────────────────────────────
    form_alumno = AlumnoForm(request.POST or None)
    if request.method == 'POST' and 'btn_inscribir' in request.POST:
        if form_alumno.is_valid():
            nuevo_alumno = form_alumno.save(creador=request.user, grupo=grupo)
            messages.success(
                request,
                f"Inscrito: {nuevo_alumno.username} | Pass: {nuevo_alumno.password_plana}"
            )
            return redirect('detalle_grupo', pk=pk)
 
    # ── Formulario Materia ────────────────────────────────────────────
    form_mat = AsignaturaForm(request.POST or None, plantel=request.user.plantel)
    if request.method == 'POST' and 'btn_materia' in request.POST:
        if form_mat.is_valid():
            mat = form_mat.save(commit=False)
            mat.save()
            mat.grupos.add(grupo)
            messages.success(request, "Materia asignada al grupo.")
            return redirect('detalle_grupo', pk=pk)
 
    alertas = []
    if not grupo.asignaturas.exists():
        alertas.append("Falta asignar docentes/materias.")
    if grupo.capacidad_maxima > 0 and alumnos_base.count() >= grupo.capacidad_maxima:
        alertas.append("Aula llena.")
 
    return render(request, 'academic/grupo_detail.html', {
        'grupo':            grupo,
        'alumnos':          page_obj,       # ahora es page_obj, compatible con {% for %}
        'page_obj':         page_obj,       # para el include de paginación
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
    
    # Traemos las carreras y pre-cargamos las asignaturas vinculadas a sus grupos
    # Así es como debe quedar:
    carreras = Carrera.objects.prefetch_related('grupos__asignaturas').all()
    context = {
        'carreras': carreras,
        **ctx,
    }
    return render(request, 'academic/lista_asignaturas.html', context)
def crear_materia(request):
    plantel = request.user.plantel
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, plantel=plantel)
        if form.is_valid():
            # 1. Extraemos los datos del formulario
            nombre = form.cleaned_data['nombre']
            clave = form.cleaned_data['clave']
            creditos = form.cleaned_data['creditos']
            grado = form.cleaned_data['grado_destino']
            nivel = form.cleaned_data['nivel_academico']
            docentes_seleccionados = form.cleaned_data['docentes']

            # 2. Buscamos TODOS los grupos (A, B, etc.) que coincidan con el grado y nivel
            # Esto traerá al Grupo A y al Grupo B automáticamente
            grupos_coincidentes = Grupo.objects.filter(
                plantel=plantel,
                grado=grado,
                carrera__nivel=nivel
            )

            if grupos_coincidentes.exists():
                # 3. Creamos la asignatura una sola vez
                # Usamos la carrera del primer grupo encontrado
                nueva_asignatura = Asignatura.objects.create(
                    carrera=grupos_coincidentes.first().carrera,
                    nombre=nombre,
                    clave=clave,
                    creditos=creditos
                )

                # 4. LA MAGIA: Vinculamos todos los grupos encontrados a esta materia
                nueva_asignatura.grupos.set(grupos_coincidentes)

                # 5. Vinculamos los docentes seleccionados
                if docentes_seleccionados:
                    nueva_asignatura.docentes.set(docentes_seleccionados)

                # Creamos un mensaje informativo con los nombres de los grupos (A, B...)
                nombres_grupos = ", ".join([g.nombre for g in grupos_coincidentes])
                messages.success(request, f"Materia '{nombre}' vinculada a los grupos: {nombres_grupos}")
            else:
                messages.error(request, f"No se encontraron grupos para {grado}º de {nivel}.")

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

@login_required
def detalle_alumno(request, pk):
    alumno = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='ALUMNO')
    ctx = get_plantel_context(request.user)
 
    # --- Manejar edición inline desde el modal ---
    if request.method == 'POST' and request.POST.get('accion') == 'editar':
        alumno.first_name  = request.POST.get('first_name', alumno.first_name).strip()
        alumno.last_name   = request.POST.get('last_name',  alumno.last_name).strip()
        alumno.email       = request.POST.get('email',      alumno.email).strip()
        alumno.telefono    = request.POST.get('telefono',   '').strip() or None
        alumno.direccion   = request.POST.get('direccion',  '').strip() or None
        alumno.save()
        messages.success(request, f"Perfil de {alumno.get_full_name()} actualizado.")
        return redirect('detalle_alumno', pk=pk)
 
    # --- Calificaciones ---
    from .models import Calificacion, Asistencia
    calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('asignatura').order_by('-fecha')
    promedio_alumno = calificaciones.aggregate(Avg('nota'))['nota__avg'] or 0.0
 
    # --- Asistencias ---
    asistencias = Asistencia.objects.filter(alumno=alumno).order_by('-fecha')
    total_presentes = asistencias.filter(presente=True).count()
    total_faltas    = asistencias.filter(presente=False).count()
    total_registros = asistencias.count()
    porcentaje_asistencia = (
        round((total_presentes / total_registros) * 100)
        if total_registros > 0 else 0
    )
 
    return render(request, 'academic/alumno_detalle.html', {
        'alumno': alumno,
        'calificaciones': calificaciones,
        'promedio_alumno': round(promedio_alumno, 1),
        'asistencias': asistencias,
        'total_presentes': total_presentes,
        'total_faltas': total_faltas,
        'porcentaje_asistencia': porcentaje_asistencia,
        **ctx,
    })

def regenerar_password(request, pk):
    alumno = get_object_or_404(User, pk=pk)
    nueva_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    alumno.set_password(nueva_pass)
    alumno.password_plana = nueva_pass # Aquí actualizamos el campo vacío
    alumno.save()
    
    return redirect('detalle_alumno', pk=pk)

@login_required
def gestionar_horario_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)

    dias_lista = [
        ('LU', 'Lunes'), ('MA', 'Martes'), ('MI', 'Miércoles'),
        ('JU', 'Jueves'), ('VI', 'Viernes'),
    ]
    horas = [
        "07:00", "08:00", "09:00", "10:00",
        "11:00", "12:00", "13:00", "14:00",
    ]

    horarios_qs = (
        HorarioClase.objects
        .filter(grupo=grupo, activo=True)
        .select_related('asignatura', 'maestro')
    )

    # Construimos la matriz: { "07:00": { "LU": clase_o_None, ... } }
    # Usamos hora_inicio__hour para comparar de forma robusta
    from datetime import time as dtime

    def hora_str_a_time(h: str) -> dtime:
        hh, mm = h.split(":")
        return dtime(int(hh), int(mm))

    matriz = {}
    for hora in horas:
        t = hora_str_a_time(hora)
        matriz[hora] = {}
        for dia_code, _ in dias_lista:
            clase = horarios_qs.filter(
                dia=dia_code,
                hora_inicio__hour=t.hour,
                hora_inicio__minute=t.minute,
            ).first()
            matriz[hora][dia_code] = clase

    context = {
        'grupo': grupo,
        'dias_lista': dias_lista,
        'matriz': matriz,
    }
    return render(request, 'academic/gestionar_horario.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# CREAR CLASE (Formulario de alta de horario)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def crear_clase(request):
    plantel_usuario = request.user.plantel
    theme = get_campus_theme(request.user)
    

    # Recuperamos el grupo de GET o POST
    grupo_id = request.GET.get('grupo') or request.POST.get('grupo')

    if request.method == 'POST':
        asignatura_id    = request.POST.get('asignatura')
        maestro_id       = request.POST.get('maestro')
        dias_seleccionados = request.POST.getlist('dias')
        hora_inicio      = request.POST.get('hora_inicio')
        hora_fin         = request.POST.get('hora_fin')
        aula             = request.POST.get('aula', '').strip() or 'Por definir'
        grupo_id_post    = request.POST.get('grupo')

        # ── Validaciones básicas ──────────────────────────────────────────
        if not grupo_id_post:
            messages.error(request, "Debes seleccionar un grupo.")
        elif not asignatura_id:
            messages.error(request, "Debes seleccionar una asignatura.")
        elif not maestro_id:
            messages.error(request, "Debes seleccionar un docente.")
        elif not dias_seleccionados:
            messages.warning(request, "Selecciona al menos un día.")
        elif not hora_inicio or not hora_fin:
            messages.error(request, "Las horas de inicio y fin son obligatorias.")
        else:
            try:
                grupo      = get_object_or_404(Grupo,      id=grupo_id_post, plantel=plantel_usuario)
                asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                maestro    = get_object_or_404(User,       id=maestro_id)

                creados  = 0
                errores  = []

                for dia_code in dias_seleccionados:
                    try:
                        HorarioClase.objects.create(
                            grupo=grupo,
                            asignatura=asignatura,
                            maestro=maestro,
                            dia=dia_code,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            aula=aula,
                        )
                        creados += 1
                    except ValidationError as ve:
                        # Extraemos el mensaje limpio del ValidationError
                        errores.append(_extraer_mensaje_ve(ve))

                if creados:
                    messages.success(
                        request,
                        f"✅ {creados} bloque(s) guardados para {grupo.nombre}."
                    )
                for err in errores:
                    messages.error(request, f"⚠️ {err}")

                # Redirigimos si al menos algo se guardó
                if creados:
                    return redirect('gestionar_horario', grupo_id=grupo.id)

            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

    # ── Preparación del contexto (GET y POST fallido) ──────────────────────
    grupo_seleccionado = None
    if grupo_id:
        grupo_seleccionado = (
            Grupo.objects
            .filter(id=grupo_id, plantel=plantel_usuario)
            .first()
        )

    context = {
        'grupo_seleccionado': grupo_seleccionado,
        'grupos':      Grupo.objects.filter(plantel=plantel_usuario).order_by('grado', 'nombre'),
        'asignaturas': Asignatura.objects.filter(carrera__plantel=plantel_usuario).distinct(),
        # ✅ CORRECCIÓN: filtrar por rol='DOCENTE', no por is_staff
        'maestros':    User.objects.filter(plantel=plantel_usuario, rol='DOCENTE').order_by('first_name'),
        'dia_preselect':  request.GET.get('dia', ''),
        'hora_preselect': request.GET.get('hora', ''),
        'dias_opciones': [
            ('LU', 'Lunes'), ('MA', 'Martes'), ('MI', 'Miércoles'),
            ('JU', 'Jueves'), ('VI', 'Viernes'), ('SA', 'Sábado'),
        ],
        **theme
    }
    return render(request, 'academic/form_clase.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# ELIMINAR CLASE
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def eliminar_clase(request, clase_id):
    clase = get_object_or_404(HorarioClase, id=clase_id)

    if request.method == 'POST':
        grupo_id = clase.grupo_id
        clase.delete()
        messages.success(request, "Clase eliminada correctamente.")
        return redirect('gestionar_horario', grupo_id=grupo_id)

    # Si alguien llega por GET, lo mandamos de vuelta
    return redirect('gestionar_horario', grupo_id=clase.grupo_id)


# ─────────────────────────────────────────────────────────────────────────────
# CARGA HORARIA DEL ALUMNO
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def carga_horaria_alumno(request):
    alumno = request.user
    theme = get_campus_theme(request.user)

    grupo = getattr(alumno, 'alumno_grupo', None)

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

    context = {
        'alumno':   alumno,
        'horarios': horarios,
        'color':    'indigo',
        **theme
    }
    return render(request, 'academic/carga_horaria.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES INTERNAS
# ─────────────────────────────────────────────────────────────────────────────
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

@login_required
def editar_alumno(request, pk):
    ctx = get_plantel_context(request.user)
    alumno = get_object_or_404(
        User,
        pk=pk,
        plantel=request.user.plantel,
        rol='ALUMNO'
    )
 
    # Reutilizamos AlumnoForm pero sin regenerar contraseña
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
 
    return render(request, 'academic/editar_alumno.html', {
        'form': form,
        'alumno': alumno,
        **ctx,
    })
 