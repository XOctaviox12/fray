from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import User
from .forms import (
    PlantelForm, DirectorCreationForm, AlumnoRegistrationForm, 
    UserProfileForm, CoordinadorForm, ResetPasswordForm, DocenteForm
)

# --- UTILIDADES DE SEGURIDAD Y CONTEXTO ---

def is_admin(user):
    return user.is_superuser

def get_campus_theme(user):
    """Retorna etiquetas y colores según el tipo de plantel logueado."""
    if not user.plantel:
        return {'color': 'blue', 'labels': {'docente': 'Docente', 'grupo': 'Grupo', 'alumnos': 'Alumnos'}}
    
    # Plantel 2 = Universidad (Superior), Otros = Básica
    es_uni = user.plantel.id == 2
    return {
        'color': 'purple' if es_uni else 'blue',
        'labels': {
            'docente': 'Catedrático' if es_uni else 'Docente',
            'grupo': 'Facultad/Carrera' if es_uni else 'Grupo Escolar',
            'alumnos': 'Universitarios' if es_uni else 'Alumnos'
        }
    }

# --- SECCIÓN SÚPER ADMIN ---

@user_passes_test(is_admin)
def crear_plantel(request):
    if request.method == 'POST':
        form = PlantelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Nuevo plantel registrado.")
            return redirect('crear_director')
    else:
        form = PlantelForm()
    return render(request, 'users/crear_plantel.html', {'form': form})

@user_passes_test(is_admin)
def crear_director(request):
    if request.method == 'POST':
        form = DirectorCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.rol = 'DIRECTOR'
            user.save()
            messages.success(request, f"Director asignado con éxito.")
            return redirect('dashboard')
    else:
        form = DirectorCreationForm()
    return render(request, 'users/crear_director.html', {'form': form})

# --- SECCIÓN DE PERFIL ---

@login_required
def perfil_view(request):
    theme = get_campus_theme(request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            new_pwd = form.cleaned_data.get('password')
            if new_pwd:
                user.set_password(new_pwd)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Perfil actualizado.")
            return redirect('perfil')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'users/perfil.html', {'form': form, **theme})

# --- GESTIÓN DE ALUMNOS ---

@login_required
def register_alumno(request):
    theme = get_campus_theme(request.user)
    if request.method == 'POST':
        form = AlumnoRegistrationForm(request.POST)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.set_password(form.cleaned_data['password'])
            alumno.rol = 'ALUMNO'
            alumno.plantel = request.user.plantel
            alumno.save()
            messages.success(request, f"{theme['labels']['alumnos']} inscrito.")
            return redirect('dashboard')
    else:
        form = AlumnoRegistrationForm()
    return render(request, 'users/register_alumno.html', {'form': form, **theme})

# --- CRUD DE COORDINADORES ---

@login_required
def lista_coordinadores(request):
    theme = get_campus_theme(request.user)
    coordinadores = User.objects.filter(plantel=request.user.plantel, rol='COORD').order_by('-date_joined')
    return render(request, 'users/coordinadores_list.html', {'coordinadores': coordinadores, **theme})

@login_required
def crear_coordinador(request):
    theme = get_campus_theme(request.user)
    if request.method == 'POST':
        form = CoordinadorForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.rol = 'COORD'
            user.plantel = request.user.plantel
            user.save()
            messages.success(request, "Coordinador registrado.")
            return redirect('lista_coordinadores')
    else:
        form = CoordinadorForm()
    return render(request, 'users/coordinador_form.html', {'form': form, 'titulo': 'Nuevo Coordinador', **theme})

@login_required
def detalle_coordinador(request, pk):
    theme = get_campus_theme(request.user)
    coordinador = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='COORD')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            coordinador.set_password(form.cleaned_data['password'])
            coordinador.save()
            messages.success(request, "Contraseña actualizada.")
            return redirect('detalle_coordinador', pk=pk)
    else:
        form = ResetPasswordForm()
    return render(request, 'users/coordinador_detail.html', {'coord': coordinador, 'form': form, **theme})

@login_required
def editar_coordinador(request, pk):
    theme = get_campus_theme(request.user)
    coordinador = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='COORD')
    
    if request.method == 'POST':
        form = CoordinadorForm(request.POST, request.FILES, instance=coordinador)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Coordinador actualizado.")
            return redirect('lista_coordinadores')
    else:
        form = CoordinadorForm(instance=coordinador)
    return render(request, 'users/coordinador_form.html', {'form': form, 'titulo': 'Editar Coordinador', **theme})

@login_required
def eliminar_coordinador(request, pk):
    coordinador = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='COORD')
    coordinador.delete()
    messages.warning(request, "Coordinador eliminado.")
    return redirect('lista_coordinadores')

# --- CRUD DE DOCENTES ---

@login_required
def lista_docentes(request):
    theme = get_campus_theme(request.user)
    docentes = User.objects.filter(plantel=request.user.plantel, rol='DOCENTE').order_by('last_name')
    return render(request, 'users/docentes_list.html', {'docentes': docentes, **theme})

@login_required
def crear_docente(request):
    theme = get_campus_theme(request.user)
    if request.method == 'POST':
        form = DocenteForm(request.POST, request.FILES)
        if form.is_valid():
            docente = form.save(commit=False)
            docente.plantel = request.user.plantel
            docente.save()
            messages.success(request, f"{theme['labels']['docente']} registrado.")
            return redirect('lista_docentes')
    else:
        form = DocenteForm()
    return render(request, 'users/docente_form.html', {'form': form, 'titulo': f"Nuevo {theme['labels']['docente']}", **theme})

@login_required
def detalle_docente(request, pk):
    theme = get_campus_theme(request.user)
    docente = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='DOCENTE')
    return render(request, 'users/docente_detail.html', {'docente': docente, **theme})

@login_required
def editar_docente(request, pk):
    theme = get_campus_theme(request.user)
    docente = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='DOCENTE')
    if request.method == 'POST':
        form = DocenteForm(request.POST, request.FILES, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, "Docente actualizado.")
            return redirect('detalle_docente', pk=docente.pk)
    else:
        form = DocenteForm(instance=docente)
    return render(request, 'users/docente_form.html', {'form': form, 'titulo': f"Editar {theme['labels']['docente']}", **theme})

@login_required
def eliminar_docente(request, pk):
    docente = get_object_or_404(User, pk=pk, plantel=request.user.plantel, rol='DOCENTE')
    docente.delete()
    messages.warning(request, "Docente eliminado.")
    return redirect('lista_docentes')

def get_campus_theme(user):
    if not user.plantel:
        return {'color': 'blue', 'labels': {'docente': 'Docente', 'docentes': 'Docentes', 'grupos': 'Grupos'}}
    
    es_uni = user.plantel.id == 2
    return {
        'color': 'purple' if es_uni else 'blue',
        'labels': {
            'docente': 'Catedrático' if es_uni else 'Docente',
            'docentes': 'Catedráticos' if es_uni else 'Docentes', 
            'grupo': 'Facultad/Carrera' if es_uni else 'Grupo Escolar',
            'grupos': 'Facultades/Carreras' if es_uni else 'Grupos', 
            'alumnos': 'Universitarios' if es_uni else 'Alumnos'
        }
    }