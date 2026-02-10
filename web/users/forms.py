# web/users/forms.py
from django import forms
from .models import User
from django.core.exceptions import ValidationError
from campuses.models import Plantel

class UserProfileForm(forms.ModelForm):
    password = forms.CharField(
        required=False, 
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Nueva contraseña'
        })
    )
    confirm_password = forms.CharField(
        required=False, 
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Repite la contraseña'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'fecha_nacimiento', 'foto_perfil']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'rows': '2'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
    


class PlantelForm(forms.ModelForm):
    class Meta:
        model = Plantel
        fields = ['nombre', 'direccion', 'color_tema']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border', 'rows': 3}),
            'color_tema': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20'}),
        }

class DirectorCreationForm(forms.ModelForm):
    plantel = forms.ModelChoiceField(
        queryset=Plantel.objects.all(),
        empty_label="Selecciona un plantel",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'Contraseña'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'plantel', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'Usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border', 'placeholder': 'Número telefónico'}),
        }
        

class AlumnoRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Contraseña temporal'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none', 'placeholder': 'Matrícula o Usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none', 'placeholder': 'Nombre(s)'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none', 'placeholder': 'correo@ejemplo.com'}),
        }

class CoordinadorForm(forms.ModelForm):
    password = forms.CharField(
        required=False, 
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Asignar contraseña'})
    )
    confirm_password = forms.CharField(
        required=False, 
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Repetir contraseña'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'fecha_nacimiento', 'foto_perfil']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Matrícula o usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Nombre(s)'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '10 dígitos'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'rows': '2'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
        }

    def clean_foto_perfil(self):
        """Seguridad en Archivos: Valida tamaño y extensión."""
        foto = self.cleaned_data.get('foto_perfil')
        if foto:
            # Limitar a 2MB para evitar ataques de denegación de servicio (DoS) por peso
            if foto.size > 2 * 1024 * 1024:
                raise ValidationError("La imagen es demasiado pesada (máximo 2MB).")
            
            # Validar extensión para evitar ejecución de scripts (RCE)
            extension = foto.name.split('.')[-1].lower()
            if extension not in ['jpg', 'jpeg', 'png']:
                raise ValidationError("Solo se permiten formatos JPG o PNG.")
        return foto

    def clean_username(self):
        """Prevención de XSS: Limpia caracteres especiales en el usuario."""
        username = self.cleaned_data.get('username')
        
        if not username.isalnum():
            raise ValidationError("El nombre de usuario solo debe contener letras y números.")
        return username
    

class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Nueva contraseña'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Repite la contraseña'})
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
    
class DocenteForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña Provisional",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-purple-500', 'placeholder': '••••••••'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'direccion', 'foto_perfil']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'placeholder': 'Matrícula o ID'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'placeholder': 'Nombre(s)'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'placeholder': '10 dígitos'}),
            'direccion': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-200', 'rows': 2}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.rol = 'DOCENTE'  # Forzamos el rol aquí
        if commit:
            user.save()
        return user