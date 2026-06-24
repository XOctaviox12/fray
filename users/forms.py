from django import forms
from django.contrib.auth import get_user_model
from campuses.models import Plantel

User = get_user_model()

INPUT = (
    "w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 "
    "text-sm text-slate-800 placeholder-slate-400 outline-none "
    "focus:ring-2 focus:ring-indigo-500 focus:border-transparent "
    "focus:bg-white transition-all"
)

DATE_INPUT = INPUT + " appearance-none"


# ── Plantel ────────────────────────────────────────────────────────────────
class PlantelForm(forms.ModelForm):
    class Meta:
        model = Plantel
        fields = ["nombre", "direccion", "nivel_educativo", "total_aulas"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT, "placeholder": "Ej. Plantel Norte"}),
            "direccion": forms.Textarea(attrs={"class": INPUT, "rows": 3}),
            "nivel_educativo": forms.Select(attrs={"class": INPUT}),
            "total_aulas": forms.NumberInput(attrs={"class": INPUT}),
        }


# ── Director ───────────────────────────────────────────────────────────────
class DirectorCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Contraseña provisional"}),
        label="Contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "plantel", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT}),
            "first_name": forms.TextInput(attrs={"class": INPUT}),
            "last_name": forms.TextInput(attrs={"class": INPUT}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "plantel": forms.Select(attrs={"class": INPUT}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.rol = "DIRECTOR"
        if commit:
            user.save()
        return user


# ── Alumno ─────────────────────────────────────────────────────────────────
class AlumnoRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Contraseña provisional"}),
        label="Contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "telefono",
                  "fecha_nacimiento", "direccion", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT, "placeholder": "Matrícula"}),
            "first_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Nombre(s)"}),
            "last_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Apellidos"}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "telefono": forms.TextInput(attrs={"class": INPUT}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": DATE_INPUT, "type": "date"}),
            "direccion": forms.TextInput(attrs={"class": INPUT}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.rol = "ALUMNO"
        if commit:
            user.save()
        return user


# ── Perfil propio ──────────────────────────────────────────────────────────
class UserProfileForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Dejar vacío para no cambiar"}),
        label="Nueva contraseña",
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Confirmar nueva contraseña"}),
        label="Confirmar contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email",
                  "telefono", "fecha_nacimiento", "direccion", "foto_perfil"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT}),
            "first_name": forms.TextInput(attrs={"class": INPUT}),
            "last_name": forms.TextInput(attrs={"class": INPUT}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "telefono": forms.TextInput(attrs={"class": INPUT}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": DATE_INPUT, "type": "date"}),
            "direccion": forms.TextInput(attrs={"class": INPUT}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned


# ── Coordinador ────────────────────────────────────────────────────────────
class CoordinadorForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Contraseña (dejar vacío para no cambiar)"}),
        label="Contraseña",
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Confirmar contraseña"}),
        label="Confirmar contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email",
                  "telefono", "fecha_nacimiento", "direccion", "foto_perfil"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT}),
            "first_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Nombre(s)"}),
            "last_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Apellidos"}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "telefono": forms.TextInput(attrs={"class": INPUT}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": DATE_INPUT, "type": "date"}),
            "direccion": forms.TextInput(attrs={"class": INPUT}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


# ── Reset password (para detalle coordinador/docente) ─────────────────────
class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Nueva contraseña"}),
        label="Nueva contraseña",
        min_length=6,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Confirmar contraseña"}),
        label="Confirmar contraseña",
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned


# ── Docente ────────────────────────────────────────────────────────────────
class DocenteForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "Contraseña (dejar vacío para no cambiar)"}),
        label="Contraseña",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email",
                  "telefono", "direccion", "foto_perfil", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT, "placeholder": "Matrícula docente"}),
            "first_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Nombre(s)"}),
            "last_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Apellidos"}),
            "email": forms.EmailInput(attrs={"class": INPUT}),
            "telefono": forms.TextInput(attrs={"class": INPUT}),
            "direccion": forms.TextInput(attrs={"class": INPUT}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = "DOCENTE"
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        elif not user.pk:
            # nuevo docente sin contraseña → inutilizable hasta que la pongan
            user.set_unusable_password()
        if commit:
            user.save()
        return user