from django import forms
from .models import Grupo, Asignatura, Carrera, Periodo, HorarioClase
from users.models import User, Tutor
import random
import string
from django.contrib.auth import get_user_model

User = get_user_model()

INPUT_CLASSES = (
    "w-full px-4 py-3 rounded-xl "
    "border border-slate-200 "
    "bg-slate-50/50 "
    "text-sm text-slate-900 "
    "placeholder-slate-400 "
    "focus:bg-white "
    "focus:border-indigo-500 "
    "focus:ring-2 focus:ring-indigo-500 "
    "focus:outline-none "
    "transition-all duration-200 "
    "hover:bg-white"
)
class GrupoForm(forms.ModelForm):
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

    # Nombres por defecto si el nivel aún no tiene Carrera creada en este plantel
    NIVELES_BASE = [
        ('SECUNDARIA', 'Secundaria General'),
        ('PREPARATORIA', 'Preparatoria General'),
        ('UNIVERSIDAD', 'Universidad General'),
    ]

    def __init__(self, *args, **kwargs):
        plantel = kwargs.pop('plantel', None)
        super().__init__(*args, **kwargs)

        if plantel:
            # Aseguramos que el plantel tenga las 3 carreras base.
            # get_or_create no duplica: si ya existe una Carrera con ese
            # nivel para este plantel, la respeta tal cual está.
            for nivel, nombre_default in self.NIVELES_BASE:
                Carrera.objects.get_or_create(
                    plantel=plantel,
                    nivel=nivel,
                    defaults={'nombre': nombre_default}
                )

            self.fields['carrera'].queryset = Carrera.objects.filter(plantel=plantel)
            self.fields['docentes'].queryset = User.objects.filter(plantel=plantel, rol='DOCENTE')
            self.fields['carrera'].empty_label = "--- Seleccione Nivel (Secu o Prepa) ---"


class AsignaturaForm(forms.ModelForm):
    # Coincide exactamente con Carrera.NIVELES del modelo
    NIVELES_ASIGNATURA = [
        ('', '--- Seleccione Nivel ---'),
        ('SECUNDARIA', 'Secundaria'),
        ('PREPARATORIA', 'Preparatoria'),
        ('UNIVERSIDAD', 'Universidad'),
    ]

    nivel_academico = forms.ChoiceField(
        choices=NIVELES_ASIGNATURA,
        widget=forms.Select(attrs={
            'id': 'id_nivel_selector',
            'class': (
                'w-full bg-slate-50 border border-slate-200 rounded-xl '
                'px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 '
                'font-bold text-slate-700'
            ),
        }),
        label="¿Para qué nivel es la materia?",
        required=True,
    )

    # Marcado por defecto: la materia se asigna sola a TODOS los grupos
    # que tengan ese nivel dentro del plantel.
    todos_los_grupos = forms.BooleanField(
        required=False,
        initial=True,
        label="Asignar automáticamente a todos los grupos de este nivel",
        widget=forms.CheckboxInput(attrs={'id': 'id_todos_los_grupos'}),
    )

    # Solo se usa si el usuario desmarca "todos_los_grupos".
    grupos = forms.ModelMultipleChoiceField(
        queryset=Grupo.objects.none(),
        required=False,
        label="O elige grupos específicos de ese nivel",
        widget=forms.CheckboxSelectMultiple(),
    )

    docentes = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="Docentes que imparten la materia",
        required=False,
    )

    class Meta:
        model = Asignatura
        fields = ['nombre', 'clave', 'creditos', 'docentes']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': (
                    'w-full bg-white border border-slate-200 rounded-xl '
                    'px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500'
                ),
                'placeholder': 'Ej: Matemáticas I',
            }),
            'clave': forms.TextInput(attrs={
                'class': (
                    'w-full bg-white border border-slate-200 rounded-xl '
                    'px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500'
                ),
                'placeholder': 'Clave interna',
            }),
            'creditos': forms.NumberInput(attrs={
                'class': (
                    'w-full bg-white border border-slate-200 rounded-xl '
                    'px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500'
                ),
            }),
        }

    def __init__(self, *args, **kwargs):
        plantel = kwargs.pop('plantel', None)
        super().__init__(*args, **kwargs)

        if plantel:
            self.fields['docentes'].queryset = User.objects.filter(
                plantel=plantel, rol='DOCENTE'
            )
            # Todos los grupos del plantel; el JS filtra visualmente por
            # nivel usando data-nivel, y clean() vuelve a filtrar en server.
            self.fields['grupos'].queryset = Grupo.objects.filter(
                plantel=plantel
            ).select_related('carrera').order_by('carrera__nivel', 'grado', 'nombre')

            if hasattr(plantel, 'nivel_educativo') and plantel.nivel_educativo != 'SUPERIOR':
                self.fields['creditos'].widget = forms.HiddenInput()
                self.fields['creditos'].required = False

    def clean(self):
        cleaned = super().clean()
        nivel = cleaned.get('nivel_academico')
        todos = cleaned.get('todos_los_grupos')
        grupos = cleaned.get('grupos')

        if not nivel:
            return cleaned

        if not todos and not grupos:
            raise forms.ValidationError(
                "Selecciona al menos un grupo específico, o marca la casilla "
                "para asignar la materia a todos los grupos de ese nivel."
            )

        # Si eligieron grupos a mano, nos aseguramos de que de verdad
        # pertenezcan al nivel elegido (por si el JS falla o lo manipulan).
        if not todos and grupos:
            fuera_de_nivel = grupos.exclude(carrera__nivel=nivel)
            if fuera_de_nivel.exists():
                raise forms.ValidationError(
                    "Uno o más grupos seleccionados no pertenecen al nivel elegido."
                )

        return cleaned

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 
                'placeholder': 'Escribe los nombres'
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 
                'placeholder': 'Escribe los apellidos'
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASSES, 
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 
                'placeholder': 'Ej. 5512345678'
            }),
            'direccion': forms.TextInput(attrs={
                'class': INPUT_CLASSES, 
                'placeholder': 'Calle, número y colonia'
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
        while True:
            sufijo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            nuevo_username = f"fray{sufijo}"
            if not User.objects.filter(username=nuevo_username).exists():
                alumno.username = nuevo_username
                break
        password_aleatoria = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        alumno.set_password(password_aleatoria)              # hash real de Django + bcrypt (password_verificacion)
        alumno.set_password_recuperable(password_aleatoria)   # ← esta línea faltaba
        if commit:
            alumno.save()
        return alumno, password_aleatoria # ← ahora retorna tupla (alumno, contraseña)
class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['nombre', 'telefono']

class HorarioClaseForm(forms.ModelForm):
    class Meta:
        model = HorarioClase
        fields = ['asignatura', 'maestro', 'aula', 'dia', 'hora_inicio', 'hora_fin', 'grupo']
        widgets = {
            'dia': forms.HiddenInput(),
            'hora_inicio': forms.HiddenInput(),
            'grupo': forms.HiddenInput(),
            'hora_fin': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'w-full px-4 py-3 rounded-2xl border border-slate-200 bg-slate-50/50 outline-none focus:ring-2 focus:ring-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        # 1. Extraemos el plantel enviado desde la vista
        plantel = kwargs.pop('plantel', None)
        super().__init__(*args, **kwargs)
        
        # 2. Filtro Base de Maestros (Asegúrate que en la DB sea 'DOCENTE' en mayúsculas)
        maestros_qs = User.objects.filter(rol='DOCENTE')
        
        if plantel:
            maestros_qs = maestros_qs.filter(plantel=plantel)
            # También filtramos las asignaturas por plantel
            self.fields['asignatura'].queryset = Asignatura.objects.filter(carrera__plantel=plantel).distinct()

        self.fields['maestro'].queryset = maestros_qs.order_by('first_name')

        # 3. PERSONALIZACIÓN DE TEXTO (Lo que pediste)
        # Mostrar: "Matemática - Carrera (Grados: 1, 2)"
        self.fields['asignatura'].label_from_instance = lambda obj: (
            f"{obj.nombre} - {obj.carrera.nombre} "
            f"(Grados: {', '.join([str(g.grado) for g in obj.grupos.all()])})"
        )

        # Mostrar: "Juan Pérez - Docente"
        self.fields['maestro'].label_from_instance = lambda obj: (
            f"{obj.get_full_name() or obj.username} - {obj.rol.capitalize()}"
        )

        # 4. Estética y Placeholders
        self.fields['asignatura'].empty_label = "--- Selecciona la Materia ---"
        self.fields['maestro'].empty_label = "--- Selecciona al Docente ---"
        
        # Aplicar clases CSS de forma masiva
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                # Usamos la constante INPUT_CLASSES que definiste arriba
                current_classes = field.widget.attrs.get('class', '')
                field.widget.attrs.update({
                    'class': f"{current_classes} {INPUT_CLASSES}".strip()
                })
            
            if self.errors.get(field_name):
                field.widget.attrs['class'] += ' border-rose-300 ring-rose-100 bg-rose-50'

    def clean(self):
        cleaned_data = super().clean()
        # Aquí puedes agregar validaciones de choque de horario más tarde
        return cleaned_data