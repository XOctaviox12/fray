from django import forms
from academic.models import Grupo, Asignatura, Carrera, Periodo, HorarioClase
from academic.models import (
    Tarea, Actividad, Asistencia, EvaluacionParcial,
    CierreParcial, BoletaParcial
)
from users.models import User, Tutor
import random
import string
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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
class TareaForm(forms.ModelForm):
    """Formulario para crear/editar Tareas.
    
    El campo `periodo` se auto-completa en el modelo.save() desde grupo.periodo.
    No se edita manualmente.
    """
    
    class Meta:
        model = Tarea
        fields = ['grupo', 'asignatura', 'titulo', 'descripcion', 'archivo', 'fecha_entrega', 'parcial']
        widgets = {
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'titulo': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Título de la tarea',
                'required': True,
            }),
            'descripcion': forms.Textarea(attrs={
                'class': f"{INPUT_CLASSES} min-h-[100px]",
                'placeholder': 'Instrucciones detalladas',
                'rows': 4,
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': INPUT_CLASSES,
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.png,.zip',
            }),
            'fecha_entrega': forms.DateTimeInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'datetime-local',
                'required': True,
            }),
            'parcial': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'min': 1,
                'max': 4,
                'value': 1,
            }),
        }
    
    def __init__(self, *args, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if docente:
            # Docente solo ve sus grupos
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('carrera', 'periodo').order_by('grado', 'nombre')
            
            # Docente solo ve sus asignaturas
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            ).order_by('nombre')
        else:
            self.fields['grupo'].queryset = Grupo.objects.all().select_related('carrera', 'periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        # Etiquetas amigables
        self.fields['grupo'].label = "Grupo"
        self.fields['asignatura'].label = "Materia"
        self.fields['parcial'].label = "Parcial (1-4)"
    
    def clean(self):
        cleaned = super().clean()
        grupo = cleaned.get('grupo')
        
        # Validación: si el periodo del grupo está cerrado, rechazar
        if grupo and grupo.periodo and not grupo.periodo.activo:
            raise ValidationError(
                f'El ciclo "{grupo.periodo}" ya fue cerrado por el director. '
                'No se pueden crear nuevas tareas.'
            )
        
        return cleaned
 
 
# ═════════════════════════════════════════════════════════════════════════════
# 2. FORMULARIOS DE ACTIVIDAD
# ═════════════════════════════════════════════════════════════════════════════
 
class ActividadForm(forms.ModelForm):
    """Formulario para crear/editar Actividades.
    
    El campo `periodo` se auto-completa en el modelo.save() desde grupo.periodo.
    """
    
    class Meta:
        model = Actividad
        fields = [
            'grupo', 'asignatura', 'titulo', 'instrucciones', 'tipo',
            'archivo', 'url_interactiva', 'fecha_entrega', 'valor_total',
            'calificacion_automatica', 'parcial'
        ]
        widgets = {
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'titulo': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Título de la actividad',
                'required': True,
            }),
            'instrucciones': forms.Textarea(attrs={
                'class': f"{INPUT_CLASSES} min-h-[100px]",
                'placeholder': 'Instrucciones para los alumnos',
                'rows': 4,
            }),
            'tipo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': INPUT_CLASSES,
                'accept': '.pdf,.doc,.docx,.jpg,.png,.zip',
            }),
            'url_interactiva': forms.URLInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'https://www.geogebra.org/... o similar',
            }),
            'fecha_entrega': forms.DateTimeInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'datetime-local',
                'required': True,
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'value': '10',
            }),
            'calificacion_automatica': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-slate-300',
            }),
            'parcial': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'min': 1,
                'max': 4,
                'value': 1,
            }),
        }
    
    def __init__(self, *args, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('carrera', 'periodo').order_by('grado', 'nombre')
            
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            ).order_by('nombre')
        else:
            self.fields['grupo'].queryset = Grupo.objects.all().select_related('carrera', 'periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        self.fields['grupo'].label = "Grupo"
        self.fields['asignatura'].label = "Materia"
        self.fields['tipo'].label = "Tipo de Actividad"
        self.fields['calificacion_automatica'].label = "¿Calificar automáticamente?"
        self.fields['parcial'].label = "Parcial (1-4)"
    
    def clean(self):
        cleaned = super().clean()
        grupo = cleaned.get('grupo')
        
        if grupo and grupo.periodo and not grupo.periodo.activo:
            raise ValidationError(
                f'El ciclo "{grupo.periodo}" ya fue cerrado por el director. '
                'No se pueden crear nuevas actividades.'
            )
        
        return cleaned
 
 
# ═════════════════════════════════════════════════════════════════════════════
# 3. FORMULARIOS DE ASISTENCIA
# ═════════════════════════════════════════════════════════════════════════════
 
class AsistenciaForm(forms.ModelForm):
    """Formulario para crear/editar un registro de Asistencia.
    
    El campo `periodo` se auto-completa en el modelo.save() desde grupo.periodo.
    """
    
    class Meta:
        model = Asistencia
        fields = ['alumno', 'grupo', 'asignatura', 'fecha', 'estado', 'parcial']
        widgets = {
            'alumno': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': False,
            }),
            'fecha': forms.DateInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'date',
                'required': True,
            }),
            'estado': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'parcial': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'min': 1,
                'max': 4,
                'value': 1,
            }),
        }
    
    def __init__(self, *args, docente=None, grupo=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si vienen desde una vista de grupo específica, filtrar
        if grupo:
            self.fields['grupo'].initial = grupo
            self.fields['grupo'].queryset = Grupo.objects.filter(pk=grupo.pk)
            self.fields['alumno'].queryset = User.objects.filter(
                alumno_grupo=grupo, rol='ALUMNO'
            ).order_by('last_name', 'first_name')
            self.fields['asignatura'].queryset = grupo.asignaturas.all()
        elif docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            )
        else:
            self.fields['grupo'].queryset = Grupo.objects.all().select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        self.fields['alumno'].label = "Alumno"
        self.fields['estado'].label = "Estado"
        self.fields['parcial'].label = "Parcial (1-4)"
    
    def clean(self):
        cleaned = super().clean()
        grupo = cleaned.get('grupo')
        
        if grupo and grupo.periodo and not grupo.periodo.activo:
            raise ValidationError(
                f'El ciclo "{grupo.periodo}" ya fue cerrado por el director. '
                'No se puede pasar lista.'
            )
        
        return cleaned
 
 
class AsistenciaLoteForm(forms.Form):
    """Formulario para registrar asistencia en lote de un grupo + fecha."""
    
    grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.all(),
        widget=forms.Select(attrs={
            'class': INPUT_CLASSES,
            'required': True,
        }),
        label="Grupo"
    )
    
    asignatura = forms.ModelChoiceField(
        queryset=Asignatura.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': INPUT_CLASSES,
        }),
        label="Materia (opcional)"
    )
    
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': INPUT_CLASSES,
            'type': 'date',
            'required': True,
        }),
        label="Fecha"
    )
    
    parcial = forms.IntegerField(
        min_value=1, max_value=4,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': INPUT_CLASSES,
            'type': 'number',
        }),
        label="Parcial (1-4)"
    )
    
    def __init__(self, *args, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            )
 
 
# ═════════════════════════════════════════════════════════════════════════════
# 4. FORMULARIOS DE EVALUACIÓN PARCIAL
# ═════════════════════════════════════════════════════════════════════════════
 
class EvaluacionParcialForm(forms.ModelForm):
    """Formulario para registrar una Evaluación Parcial (examen o proyecto).
    
    El campo `periodo` se auto-completa en el modelo.save() desde grupo.periodo.
    """
    
    class Meta:
        model = EvaluacionParcial
        fields = ['alumno', 'grupo', 'asignatura', 'rubro', 'nota', 'observacion', 'parcial']
        widgets = {
            'alumno': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'rubro': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'nota': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00 - 10.00',
            }),
            'observacion': forms.Textarea(attrs={
                'class': f"{INPUT_CLASSES} min-h-[80px]",
                'placeholder': 'Comentarios opcionales',
                'rows': 3,
            }),
            'parcial': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'min': 1,
                'max': 4,
                'value': 1,
            }),
        }
    
    def __init__(self, *args, docente=None, grupo=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if grupo:
            self.fields['grupo'].initial = grupo
            self.fields['grupo'].queryset = Grupo.objects.filter(pk=grupo.pk)
            self.fields['alumno'].queryset = User.objects.filter(
                alumno_grupo=grupo, rol='ALUMNO'
            ).order_by('last_name', 'first_name')
            self.fields['asignatura'].queryset = grupo.asignaturas.all()
        elif docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            )
        else:
            self.fields['grupo'].queryset = Grupo.objects.all().select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        self.fields['rubro'].label = "Tipo de Evaluación"
        self.fields['nota'].label = "Calificación (0-10)"
        self.fields['parcial'].label = "Parcial (1-4)"
    
    def clean(self):
        cleaned = super().clean()
        grupo = cleaned.get('grupo')
        nota = cleaned.get('nota')
        
        if grupo and grupo.periodo and not grupo.periodo.activo:
            raise ValidationError(
                f'El ciclo "{grupo.periodo}" ya fue cerrado por el director. '
                'No se pueden capturar nuevas calificaciones.'
            )
        
        if nota is not None and (nota < 0 or nota > 10):
            raise ValidationError('La calificación debe estar entre 0 y 10.')
        
        return cleaned
 
 
# ═════════════════════════════════════════════════════════════════════════════
# 5. FORMULARIOS DE CIERRE PARCIAL
# ═════════════════════════════════════════════════════════════════════════════
 
class CierreParcialForm(forms.ModelForm):
    """Formulario para registrar el cierre de un parcial.
    
    Marca que el docente ya cerró las calificaciones de un parcial específico.
    """
    
    class Meta:
        model = CierreParcial
        fields = ['grupo', 'asignatura', 'parcial']
        widgets = {
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'parcial': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
        }
    
    def __init__(self, *args, docente=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            )
        else:
            self.fields['grupo'].queryset = Grupo.objects.all()
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        # Opciones de parcial
        self.fields['parcial'].choices = [(i, f'Parcial {i}') for i in range(1, 5)]
        self.fields['parcial'].label = "¿Cuál parcial cierras?"
 
 
# ═════════════════════════════════════════════════════════════════════════════
# 6. FORMULARIOS DE BOLETA PARCIAL
# ═════════════════════════════════════════════════════════════════════════════
 
class BoletaParcialForm(forms.ModelForm):
    """Formulario para capturar la boleta parcial final (calificación integrada).
    
    El docente ingresa la calificación final después de promediar todos los rubros.
    """
    
    class Meta:
        model = BoletaParcial
        fields = [
            'alumno', 'grupo', 'asignatura', 'parcial',
            'nota_tareas', 'nota_actividades', 'nota_asistencia',
            'nota_examen', 'nota_proyecto', 'calificacion_final'
        ]
        widgets = {
            'alumno': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'grupo': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'asignatura': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'parcial': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'required': True,
            }),
            'nota_tareas': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
            }),
            'nota_actividades': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
            }),
            'nota_asistencia': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
            }),
            'nota_examen': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
            }),
            'nota_proyecto': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
            }),
            'calificacion_final': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'max': '10',
                'placeholder': '0.00',
                'required': True,
            }),
        }
    
    def __init__(self, *args, docente=None, grupo=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if grupo:
            self.fields['grupo'].initial = grupo
            self.fields['grupo'].queryset = Grupo.objects.filter(pk=grupo.pk)
            self.fields['alumno'].queryset = User.objects.filter(
                alumno_grupo=grupo, rol='ALUMNO'
            ).order_by('last_name', 'first_name')
            self.fields['asignatura'].queryset = grupo.asignaturas.all()
        elif docente:
            self.fields['grupo'].queryset = Grupo.objects.filter(
                docentes=docente
            ).select_related('periodo')
            self.fields['asignatura'].queryset = Asignatura.objects.filter(
                docentes=docente
            )
        else:
            self.fields['grupo'].queryset = Grupo.objects.all()
            self.fields['asignatura'].queryset = Asignatura.objects.all()
        
        # Opciones de parcial
        self.fields['parcial'].choices = [(i, f'Parcial {i}') for i in range(1, 5)]
        self.fields['parcial'].label = "Parcial"
        self.fields['calificacion_final'].label = "Calificación Final (0-10)"
    
    def clean(self):
        cleaned = super().clean()
        notas = [
            cleaned.get('nota_tareas'),
            cleaned.get('nota_actividades'),
            cleaned.get('nota_asistencia'),
            cleaned.get('nota_examen'),
            cleaned.get('nota_proyecto'),
        ]
        calificacion_final = cleaned.get('calificacion_final')
        
        # Validar que todas las notas estén en rango 0-10
        for nota in notas:
            if nota is not None and (nota < 0 or nota > 10):
                raise ValidationError('Todas las calificaciones deben estar entre 0 y 10.')
        
        if calificacion_final is not None and (calificacion_final < 0 or calificacion_final > 10):
            raise ValidationError('La calificación final debe estar entre 0 y 10.')
        
        return cleaned
 