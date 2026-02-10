from django import forms
from .models import Grupo, Asignatura, Carrera, Periodo
from users.models import User, Tutor

INPUT_CLASSES = (
    "w-full px-4 py-3 rounded-xl "
    "border border-slate-300 "
    "bg-slate-50 "
    "text-sm text-slate-900 "
    "placeholder-slate-400 "
    "focus:bg-white "
    "focus:border-indigo-500 "
    "focus:ring-2 focus:ring-indigo-500 "
    "focus:outline-none "
    "transition"
)

class GrupoForm(forms.ModelForm):
    # Selector de docentes (Mantenemos la cuadrícula y filtros)
    docentes = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs font-medium text-slate-600'
        }),
        required=False,
        label="Asignar Docentes"
    )

    class Meta:
        model = Grupo
        # Solo campos persistentes en la base de datos
        fields = ['carrera', 'grado', 'nombre', 'aula', 'capacidad_maxima', 'docentes']
        
        widgets = {
            'carrera': forms.Select(attrs={
                'id': 'id_carrera_grupo', 
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-purple-500 bg-white'
            }),
            'grado': forms.NumberInput(attrs={
                'id': 'id_grado_input', 
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej: 1, 3, 6...'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 
                'placeholder': 'Ej: A, B, Matutino...'
            }),
            'aula': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 
                'placeholder': 'Ej: B-102'
            }),
            'capacidad_maxima': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        plantel = kwargs.pop('plantel', None)
        super().__init__(*args, **kwargs)
        
        if plantel:
            # Filtros de seguridad para que solo aparezcan datos de tu plantel (Plantel 1)
            self.fields['carrera'].queryset = Carrera.objects.filter(plantel=plantel)
            self.fields['docentes'].queryset = User.objects.filter(plantel=plantel, rol='DOCENTE')
            
            
            # Label para guiar al usuario en la selección de Secundaria o Prepa
            self.fields['carrera'].empty_label = "--- Seleccione Nivel (Secu o Prepa) ---"



class AsignaturaForm(forms.ModelForm):
    # Paso 1: Elegir Nivel (Para filtrar grupos por carrera)
    nivel_academico = forms.ChoiceField(
        choices=[('', '--- Seleccione Nivel ---'), ('SECUNDARIA', 'Secundaria'), ('PREPARATORIA', 'Preparatoria')],
        widget=forms.Select(attrs={
            'id': 'id_nivel_selector',
            'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 font-bold text-slate-700'
        }),
        label="¿Para qué nivel es la materia?",
        required=True
    )

    # Paso 2: Grado Destino (Se usará para replicar en todos los grupos de ese grado)
    grado_destino = forms.IntegerField(
        label="Grado / Cuatrimestre",
        widget=forms.NumberInput(attrs={
            'class': 'w-full bg-white border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500', 
            'placeholder': 'Ej: 1'
        }),
        required=True
    )

    # Paso 3: Selección múltiple de docentes
    docentes = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs font-medium text-slate-600'
        }),
        label="Docentes que imparten la materia",
        required=False
    )

    class Meta:
        model = Asignatura
        # Definimos los campos que se guardarán en el modelo
        fields = ['nombre', 'clave', 'creditos', 'docentes']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500', 
                'placeholder': 'Ej: Matemáticas I'
            }),
            'clave': forms.TextInput(attrs={
                'class': 'w-full bg-white border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500', 
                'placeholder': 'Clave interna'
            }),
            'creditos': forms.NumberInput(attrs={
                'class': 'w-full bg-white border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        plantel = kwargs.pop('plantel', None)
        super().__init__(*args, **kwargs)
        
        if plantel:
            # 1. Filtro de docentes por plantel (Usando el nombre plural 'docentes')
            if 'docentes' in self.fields:
                self.fields['docentes'].queryset = User.objects.filter(plantel=plantel, rol='DOCENTE')
            
            # 2. Ocultar créditos si no es Universidad (Plantel ID 2)
            if hasattr(plantel, 'id') and plantel.id != 2:
                if 'creditos' in self.fields:
                    self.fields['creditos'].widget = forms.HiddenInput()
                    self.fields['creditos'].required = False

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nombre del alumno'
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Apellido del alumno'
            }),
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nombre de usuario'
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Teléfono de contacto'
            }),
            'direccion': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Dirección completa'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'date'
            }),
        }

    def save(self, commit=True, creador=None, grupo=None):
        alumno = super().save(commit=False)
        alumno.rol = 'ALUMNO'

        if creador:
            alumno.plantel = creador.plantel

        if grupo:
            alumno.alumno_grupo = grupo

        alumno.set_password('12345678')

        if commit:
            alumno.save()

        return alumno
    
class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['nombre', 'telefono']