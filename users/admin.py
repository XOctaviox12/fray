from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import messages
from django import forms
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.urls import path

from .models import User, Tutor
from academic.models import Grupo
from campuses.models import Plantel

import random
import string
import secrets


# ============================================================
# CONFIGURACIÓN DE CONTRASEÑAS
# ============================================================

ALFABETO_PASSWORD = (
    "ABCDEFGHJKMNPQRSTUVWXYZ"
    "abcdefghjkmnpqrstuvwxyz"
    "23456789"
)


# ============================================================
# HELPERS DE GENERACIÓN
# ============================================================

def generar_username_alumno():
    """
    Genera un usuario único para alumnos.

    Ejemplo:
        frayk82md
    """

    while True:

        sufijo = ''.join(
            random.choices(
                string.ascii_lowercase + string.digits,
                k=5
            )
        )

        candidato = f"fray{sufijo}"

        if not User.objects.filter(
            username=candidato
        ).exists():

            return candidato


def generar_matricula_docente(plantel):
    """
    Genera una matrícula única para docentes.

    Ejemplo:

        DOC-PLANTEL-001
        DOC-PLANTEL-002
        DOC-PLANTEL-003
    """

    if not plantel:
        return None

    prefijo_plantel = (
        getattr(
            plantel,
            'clave',
            None
        )
        or f"P{plantel.pk}"
    )

    prefijo = f"DOC-{prefijo_plantel}"

    ultimo_numero = 0

    existentes = User.objects.filter(
        plantel=plantel,
        rol='DOCENTE',
        username__startswith=f"{prefijo}-"
    ).values_list(
        'username',
        flat=True
    )

    for username in existentes:

        try:

            numero = int(
                username.rsplit(
                    '-',
                    1
                )[-1]
            )

            ultimo_numero = max(
                ultimo_numero,
                numero
            )

        except ValueError:
            continue

    while True:

        candidato = (
            f"{prefijo}-"
            f"{ultimo_numero + 1:03d}"
        )

        if not User.objects.filter(
            username=candidato
        ).exists():

            return candidato

        ultimo_numero += 1


def generar_password_temporal(longitud=8):
    """
    Genera una contraseña temporal segura.
    """

    return ''.join(
        secrets.choice(
            ALFABETO_PASSWORD
        )
        for _ in range(longitud)
    )


def obtener_preview(rol, plantel):
    """
    Devuelve:

        (username, password)

    para la previsualización según
    el rol y plantel.
    """

    # --------------------------------------------------------
    # ALUMNO
    # --------------------------------------------------------

    if rol == 'ALUMNO':

        return (
            generar_username_alumno(),
            generar_password_temporal()
        )

    # --------------------------------------------------------
    # DOCENTE
    # --------------------------------------------------------

    elif rol == 'DOCENTE':

        if not plantel:

            return (
                "⚠️ Selecciona un plantel",
                generar_password_temporal()
            )

        username = generar_matricula_docente(
            plantel
        )

        if not username:

            return (
                "⚠️ No se pudo generar",
                generar_password_temporal()
            )

        return (
            username,
            generar_password_temporal()
        )

    return None, None


# ============================================================
# FORMULARIO DE CREACIÓN
# ============================================================

class CustomUserCreationForm(UserCreationForm):

    alumno_grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.none(),
        required=False,
        label="Grupo (solo para alumnos)"
    )

    username_preview = forms.CharField(
        label="Usuario que se generará",
        required=False,
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
                'style': (
                    'background:#f5f5f5; '
                    'font-weight:bold;'
                )
            }
        )
    )

    password_preview = forms.CharField(
        label="Contraseña que se generará",
        required=False,
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
                'style': (
                    'background:#f5f5f5; '
                    'font-weight:bold;'
                )
            }
        )
    )

    class Meta(UserCreationForm.Meta):

        model = User

        fields = (
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'email',
            'rol',
            'plantel',
            'telefono',
            'estatus',
            'alumno_grupo',
            'username_preview',
            'password_preview',
        )

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        rol = (
            self.data.get('rol')
            if self.data
            else 'ALUMNO'
        )

        plantel_id = (
            self.data.get('plantel')
            if self.data
            else None
        )

        plantel = None

        if plantel_id:

            try:

                plantel = Plantel.objects.get(
                    id=int(plantel_id)
                )

            except (
                ValueError,
                TypeError,
                Plantel.DoesNotExist
            ):
                pass

        elif (
            self.instance.pk
            and self.instance.plantel
        ):

            plantel = self.instance.plantel

        # ----------------------------------------------------
        # FILTRAR GRUPOS POR PLANTEL
        # ----------------------------------------------------

        if plantel:

            self.fields[
                'alumno_grupo'
            ].queryset = Grupo.objects.filter(
                plantel=plantel
            )

        else:

            self.fields[
                'alumno_grupo'
            ].queryset = Grupo.objects.none()

        # ----------------------------------------------------
        # ALUMNO / DOCENTE
        # ----------------------------------------------------

        if rol in (
            'ALUMNO',
            'DOCENTE'
        ):

            self.fields[
                'username'
            ].widget = forms.HiddenInput()

            self.fields[
                'password1'
            ].widget = forms.HiddenInput()

            self.fields[
                'password2'
            ].widget = forms.HiddenInput()

            self.fields[
                'username'
            ].required = False

            self.fields[
                'password1'
            ].required = False

            self.fields[
                'password2'
            ].required = False

            preview_user, preview_pass = (
                obtener_preview(
                    rol,
                    plantel
                )
            )

            self.initial[
                'username_preview'
            ] = preview_user or ''

            self.initial[
                'password_preview'
            ] = preview_pass or ''

            self.fields[
                'username_preview'
            ].help_text = (
                "✅ Se asignará automáticamente al guardar."
            )

            self.fields[
                'password_preview'
            ].help_text = (
                "✅ Se asignará automáticamente al guardar."
            )

            if rol == 'DOCENTE':

                self.fields[
                    'plantel'
                ].required = True

        else:

            self.fields[
                'username'
            ].widget = forms.TextInput(
                attrs={
                    'class': 'vTextField'
                }
            )

            self.fields[
                'password1'
            ].widget = forms.PasswordInput(
                attrs={
                    'class': 'vTextField'
                }
            )

            self.fields[
                'password2'
            ].widget = forms.PasswordInput(
                attrs={
                    'class': 'vTextField'
                }
            )

            self.fields[
                'username'
            ].required = True

            self.fields[
                'password1'
            ].required = True

            self.fields[
                'password2'
            ].required = True

            self.initial[
                'username_preview'
            ] = ''

            self.initial[
                'password_preview'
            ] = ''

            self.fields[
                'username_preview'
            ].help_text = ''

            self.fields[
                'password_preview'
            ].help_text = ''

        # ----------------------------------------------------
        # IDs PARA JAVASCRIPT
        # ----------------------------------------------------

        self.fields[
            'rol'
        ].widget.attrs['id'] = 'id_rol'

        self.fields[
            'plantel'
        ].widget.attrs['id'] = 'id_plantel'

        self.fields[
            'username_preview'
        ].widget.attrs[
            'id'
        ] = 'id_username_preview'

        self.fields[
            'password_preview'
        ].widget.attrs[
            'id'
        ] = 'id_password_preview'

    def clean(self):

        cleaned_data = super().clean()

        rol = cleaned_data.get('rol')

        if rol in (
            'ALUMNO',
            'DOCENTE'
        ):

            self._errors.pop(
                'username',
                None
            )

            self._errors.pop(
                'password1',
                None
            )

            self._errors.pop(
                'password2',
                None
            )

            if (
                rol == 'DOCENTE'
                and not cleaned_data.get('plantel')
            ):

                raise forms.ValidationError(
                    "Debes seleccionar un plantel para el docente."
                )

        return cleaned_data


# ============================================================
# FORMULARIO DE EDICIÓN
# ============================================================

class CustomUserChangeForm(UserChangeForm):

    alumno_grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.none(),
        required=False,
        label="Grupo (solo para alumnos)"
    )

    # --------------------------------------------------------
    # NUEVA CONTRASEÑA MANUAL
    # --------------------------------------------------------

    nueva_password = forms.CharField(
        label="Nueva contraseña",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'new-password',
                'placeholder': (
                    'Dejar vacío para conservar la actual'
                ),
            }
        ),
        help_text=(
            "Si la escribes, reemplazará la contraseña actual "
            "y se guardará también como contraseña recuperable."
        )
    )

    # --------------------------------------------------------
    # PREVIEW DE CREDENCIALES
    # --------------------------------------------------------

    username_preview = forms.CharField(
        label="Usuario / matrícula actual",
        required=False,
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
                'style': (
                    'background:#f5f5f5; '
                    'font-weight:bold;'
                )
            }
        )
    )

    password_preview = forms.CharField(
        label="Contraseña actual",
        required=False,
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
                'style': (
                    'background:#f5f5f5; '
                    'font-weight:bold;'
                )
            }
        )
    )

    class Meta(UserChangeForm.Meta):

        model = User

        fields = (
            'username',
            'password',
            'nueva_password',
            'first_name',
            'last_name',
            'email',
            'rol',
            'plantel',
            'telefono',
            'estatus',
            'alumno_grupo',
            'foto_perfil',
            'password_recuperable',
            'username_preview',
            'password_preview',
        )

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        plantel = None

        # ----------------------------------------------------
        # PLANTEL SELECCIONADO
        # ----------------------------------------------------

        if 'plantel' in self.data:

            try:

                plantel_id = int(
                    self.data.get('plantel')
                )

                plantel = Plantel.objects.get(
                    id=plantel_id
                )

            except (
                ValueError,
                TypeError,
                Plantel.DoesNotExist
            ):
                pass

        elif (
            self.instance.pk
            and self.instance.plantel
        ):

            plantel = self.instance.plantel

        # ----------------------------------------------------
        # FILTRAR GRUPOS
        # ----------------------------------------------------

        if plantel:

            self.fields[
                'alumno_grupo'
            ].queryset = Grupo.objects.filter(
                plantel=plantel
            )

        else:

            self.fields[
                'alumno_grupo'
            ].queryset = Grupo.objects.none()

        # ----------------------------------------------------
        # CREDENCIALES ACTUALES
        # ----------------------------------------------------

        if self.instance.pk:

            self.initial[
                'username_preview'
            ] = (
                self.instance.username or ''
            )

            self.initial[
                'password_preview'
            ] = (
                self.instance.password_plana
                or 'No disponible'
            )

            # ------------------------------------------------
            # GUARDAR DATOS ORIGINALES PARA JS
            # ------------------------------------------------

            self.fields[
                'rol'
            ].widget.attrs[
                'data-original-role'
            ] = (
                self.instance.rol or ''
            )

            self.fields[
                'plantel'
            ].widget.attrs[
                'data-original-plantel'
            ] = (
                str(
                    self.instance.plantel_id
                    or ''
                )
            )

        # ----------------------------------------------------
        # IDs PARA JAVASCRIPT
        # ----------------------------------------------------

        self.fields[
            'rol'
        ].widget.attrs['id'] = 'id_rol'

        self.fields[
            'plantel'
        ].widget.attrs['id'] = 'id_plantel'

        self.fields[
            'username_preview'
        ].widget.attrs[
            'id'
        ] = 'id_username_preview'

        self.fields[
            'password_preview'
        ].widget.attrs[
            'id'
        ] = 'id_password_preview'

    def clean_nueva_password(self):

        password = self.cleaned_data.get(
            'nueva_password'
        )

        if password and len(password) < 8:

            raise forms.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )

        return password


# ============================================================
# ADMINISTRACIÓN DE USUARIOS
# ============================================================

class CustomUserAdmin(UserAdmin):

    add_form = CustomUserCreationForm

    form = CustomUserChangeForm

    list_display = (
        'username',
        'email',
        'rol',
        'plantel',
        'estatus',
        'is_staff',
    )

    list_filter = (
        'rol',
        'plantel',
        'estatus',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    ordering = (
        'username',
    )

    exclude = (
        'usable_password',
    )

    # ========================================================
    # URL PERSONALIZADA PARA PREVIEW
    # ========================================================

    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [

            path(
                'preview-credenciales/',
                self.admin_site.admin_view(
                    self.preview_credenciales
                ),
                name=(
                    'users_user_preview_credenciales'
                ),
            ),

        ]

        return custom_urls + urls

    # ========================================================
    # ENDPOINT PREVIEW CREDENCIALES
    # ========================================================

    def preview_credenciales(self, request):

        rol = request.GET.get(
            'rol'
        )

        plantel_id = request.GET.get(
            'plantel'
        )

        plantel = None

        if plantel_id:

            try:

                plantel = Plantel.objects.get(
                    id=int(plantel_id)
                )

            except (
                Plantel.DoesNotExist,
                ValueError,
                TypeError
            ):

                plantel = None

        username, password = obtener_preview(
            rol,
            plantel
        )

        return JsonResponse(
            {
                'username': username or '',
                'password': password or '',
            }
        )

    # ========================================================
    # FORMULARIO DE EDICIÓN
    # ========================================================

    fieldsets = (

        (
            None,
            {
                'fields': (
                    'username',
                    'password',
                    'nueva_password',
                    'username_preview',
                    'password_preview',
                )
            }
        ),

        (
            'Información personal',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'telefono',
                    'fecha_nacimiento',
                    'direccion',
                )
            }
        ),

        (
            'Información de FRAY',
            {
                'fields': (
                    'rol',
                    'plantel',
                    'estatus',
                    'alumno_grupo',
                    'foto_perfil',
                    'password_recuperable',
                )
            }
        ),

        (
            'Permisos',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            }
        ),

        (
            'Fechas importantes',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                )
            }
        ),

    )

    # ========================================================
    # FORMULARIO DE CREACIÓN
    # ========================================================

    add_fieldsets = (

        (
            None,
            {
                'classes': (
                    'wide',
                ),

                'fields': (
                    'username',
                    'password1',
                    'password2',
                    'first_name',
                    'last_name',
                    'email',
                    'rol',
                    'plantel',
                    'telefono',
                    'estatus',
                    'alumno_grupo',
                    'username_preview',
                    'password_preview',
                ),

            }
        ),

    )

    # ========================================================
    # JAVASCRIPT
    # ========================================================

    class Media:

        js = (
            'admin/js/credenciales_preview.js',
        )

    # ========================================================
    # GUARDAR USUARIO
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        self._generated_password = None

        self._generated_username = None

        self._credentials_reason = None

        # ====================================================
        # DATOS DEL FORMULARIO
        # ====================================================

        rol = form.cleaned_data.get(
            'rol'
        )

        plantel = form.cleaned_data.get(
            'plantel'
        )

        # ====================================================
        # CREACIÓN
        # ====================================================

        if not change:

            # ------------------------------------------------
            # ALUMNO / DOCENTE
            # ------------------------------------------------

            if rol in (
                'ALUMNO',
                'DOCENTE'
            ):

                username = (
                    form.cleaned_data.get(
                        'username_preview'
                    )
                    or ''
                ).strip()

                password = (
                    form.cleaned_data.get(
                        'password_preview'
                    )
                    or ''
                ).strip()

                # ------------------------------------------------
                # SI NO HAY PREVIEW, GENERAR
                # ------------------------------------------------

                if (
                    not username
                    or username.startswith('⚠️')
                ):

                    if rol == 'ALUMNO':

                        username = (
                            generar_username_alumno()
                        )

                    else:

                        if not plantel:

                            messages.error(
                                request,
                                (
                                    'Debes seleccionar un '
                                    'plantel para el docente.'
                                )
                            )

                            return

                        username = (
                            generar_matricula_docente(
                                plantel
                            )
                        )

                # ------------------------------------------------
                # CONTRASEÑA
                # ------------------------------------------------

                if (
                    not password
                    or len(password) < 8
                ):

                    password = (
                        generar_password_temporal()
                    )

                # ------------------------------------------------
                # VERIFICAR USUARIO ÚNICO
                # ------------------------------------------------

                if User.objects.filter(
                    username=username
                ).exclude(
                    pk=obj.pk
                ).exists():

                    messages.error(
                        request,
                        (
                            'El usuario/matrícula generado '
                            'ya existe. Recarga la página '
                            'y vuelve a intentarlo.'
                        )
                    )

                    return

                # ------------------------------------------------
                # GUARDAR CREDENCIALES
                # ------------------------------------------------

                obj.username = username

                obj.set_password(
                    password
                )

                obj.set_password_recuperable(
                    password
                )

                self._generated_username = (
                    username
                )

                self._generated_password = (
                    password
                )

                self._credentials_reason = (
                    'creado'
                )

            # ------------------------------------------------
            # OTROS ROLES
            # ------------------------------------------------

            else:

                if not obj.username:

                    messages.error(
                        request,
                        (
                            'Debes ingresar un '
                            'nombre de usuario para este rol.'
                        )
                    )

                    return

        # ====================================================
        # EDICIÓN
        # ====================================================

        else:

            # ------------------------------------------------
            # OBTENER DATOS ANTERIORES
            # ------------------------------------------------

            try:

                usuario_anterior = (
                    User.objects.get(
                        pk=obj.pk
                    )
                )

                rol_anterior = (
                    usuario_anterior.rol
                )

                plantel_anterior_id = (
                    usuario_anterior.plantel_id
                )

            except User.DoesNotExist:

                rol_anterior = None

                plantel_anterior_id = None

            # ------------------------------------------------
            # DETECTAR CAMBIOS
            # ------------------------------------------------

            cambio_rol = (
                rol_anterior is not None
                and rol_anterior != rol
            )

            cambio_plantel = (
                plantel_anterior_id
                != getattr(
                    plantel,
                    'pk',
                    None
                )
            )

            # =================================================
            # CAMBIO DE ROL -> DOCENTE
            # =================================================

            if (
                cambio_rol
                and rol == 'DOCENTE'
            ):

                if not plantel:

                    messages.error(
                        request,
                        (
                            'Debes seleccionar un plantel '
                            'para convertir al usuario en docente.'
                        )
                    )

                    return

                username = (
                    form.cleaned_data.get(
                        'username_preview'
                    )
                    or ''
                ).strip()

                password = (
                    form.cleaned_data.get(
                        'password_preview'
                    )
                    or ''
                ).strip()

                # ------------------------------------------------
                # FALLBACK
                # ------------------------------------------------

                if (
                    not username
                    or username.startswith('⚠️')
                ):

                    username = (
                        generar_matricula_docente(
                            plantel
                        )
                    )

                if (
                    not password
                    or len(password) < 8
                ):

                    password = (
                        generar_password_temporal()
                    )

                # ------------------------------------------------
                # VALIDAR UNICIDAD
                # ------------------------------------------------

                if User.objects.filter(
                    username=username
                ).exclude(
                    pk=obj.pk
                ).exists():

                    messages.error(
                        request,
                        (
                            'La matrícula generada ya existe. '
                            'Recarga la página y vuelve a intentarlo.'
                        )
                    )

                    return

                # ------------------------------------------------
                # ASIGNAR CREDENCIALES
                # ------------------------------------------------

                obj.username = username

                obj.set_password(
                    password
                )

                obj.set_password_recuperable(
                    password
                )

                self._generated_username = (
                    username
                )

                self._generated_password = (
                    password
                )

                self._credentials_reason = (
                    'cambio de rol a docente'
                )

            # =================================================
            # CAMBIO DE ROL -> ALUMNO
            # =================================================

            elif (
                cambio_rol
                and rol == 'ALUMNO'
            ):

                username = (
                    form.cleaned_data.get(
                        'username_preview'
                    )
                    or ''
                ).strip()

                password = (
                    form.cleaned_data.get(
                        'password_preview'
                    )
                    or ''
                ).strip()

                # ------------------------------------------------
                # FALLBACK
                # ------------------------------------------------

                if (
                    not username
                    or username.startswith('⚠️')
                ):

                    username = (
                        generar_username_alumno()
                    )

                if (
                    not password
                    or len(password) < 8
                ):

                    password = (
                        generar_password_temporal()
                    )

                # ------------------------------------------------
                # VALIDAR UNICIDAD
                # ------------------------------------------------

                if User.objects.filter(
                    username=username
                ).exclude(
                    pk=obj.pk
                ).exists():

                    messages.error(
                        request,
                        (
                            'El usuario generado ya existe. '
                            'Recarga la página y vuelve a intentarlo.'
                        )
                    )

                    return

                # ------------------------------------------------
                # ASIGNAR CREDENCIALES
                # ------------------------------------------------

                obj.username = username

                obj.set_password(
                    password
                )

                obj.set_password_recuperable(
                    password
                )

                self._generated_username = (
                    username
                )

                self._generated_password = (
                    password
                )

                self._credentials_reason = (
                    'cambio de rol a alumno'
                )

            # =================================================
            # DOCENTE CAMBIA DE PLANTEL
            # =================================================

            elif (
                rol == 'DOCENTE'
                and cambio_plantel
            ):

                if not plantel:

                    messages.error(
                        request,
                        (
                            'Debes seleccionar un plantel '
                            'para el docente.'
                        )
                    )

                    return

                username = (
                    form.cleaned_data.get(
                        'username_preview'
                    )
                    or ''
                ).strip()

                password = (
                    form.cleaned_data.get(
                        'password_preview'
                    )
                    or ''
                ).strip()

                # ------------------------------------------------
                # FALLBACK
                # ------------------------------------------------

                if (
                    not username
                    or username.startswith('⚠️')
                ):

                    username = (
                        generar_matricula_docente(
                            plantel
                        )
                    )

                if (
                    not password
                    or len(password) < 8
                ):

                    password = (
                        generar_password_temporal()
                    )

                # ------------------------------------------------
                # VALIDAR UNICIDAD
                # ------------------------------------------------

                if User.objects.filter(
                    username=username
                ).exclude(
                    pk=obj.pk
                ).exists():

                    messages.error(
                        request,
                        (
                            'La matrícula generada ya existe. '
                            'Recarga la página y vuelve a intentarlo.'
                        )
                    )

                    return

                # ------------------------------------------------
                # ASIGNAR CREDENCIALES
                # ------------------------------------------------

                obj.username = username

                obj.set_password(
                    password
                )

                obj.set_password_recuperable(
                    password
                )

                self._generated_username = (
                    username
                )

                self._generated_password = (
                    password
                )

                self._credentials_reason = (
                    'plantel de docente actualizado'
                )

            # =================================================
            # CAMBIO MANUAL DE CONTRASEÑA
            # =================================================

            else:

                nueva_password = (
                    form.cleaned_data.get(
                        'nueva_password'
                    )
                )

                if nueva_password:

                    obj.set_password(
                        nueva_password
                    )

                    obj.set_password_recuperable(
                        nueva_password
                    )

                    self._generated_username = (
                        obj.username
                    )

                    self._generated_password = (
                        nueva_password
                    )

                    self._credentials_reason = (
                        'contraseña actualizada'
                    )

        # ====================================================
        # GUARDAR EN BASE DE DATOS
        # ====================================================

        super().save_model(
            request,
            obj,
            form,
            change
        )

        # ====================================================
        # MOSTRAR CREDENCIALES
        # ====================================================

        if (
            self._generated_password
            and self._generated_username
        ):

            # ------------------------------------------------
            # TÍTULO
            # ------------------------------------------------

            if (
                self._credentials_reason
                == 'creado'
            ):

                titulo = (
                    'Usuario creado correctamente'
                )

            elif (
                self._credentials_reason
                == 'cambio de rol a docente'
            ):

                titulo = (
                    'Usuario convertido a DOCENTE correctamente'
                )

            elif (
                self._credentials_reason
                == 'cambio de rol a alumno'
            ):

                titulo = (
                    'Usuario convertido a ALUMNO correctamente'
                )

            elif (
                self._credentials_reason
                == 'plantel de docente actualizado'
            ):

                titulo = (
                    'Plantel y matrícula de DOCENTE '
                    'actualizados correctamente'
                )

            else:

                titulo = (
                    'Contraseña actualizada correctamente'
                )

            # ------------------------------------------------
            # MENSAJE
            # ------------------------------------------------

            messages.success(
                request,
                mark_safe(
                    f'''
                    <div
                        style="
                            padding:10px;
                            line-height:1.8;
                        "
                    >

                        <strong>
                            ✅ {titulo}
                        </strong>

                        <br><br>

                        👤 Usuario / matrícula:

                        <strong>
                            {self._generated_username}
                        </strong>

                        <br>

                        🔑 Contraseña:

                        <strong>
                            {self._generated_password}
                        </strong>

                        <br><br>

                        ⚠️ Guarda estas credenciales.

                        <br>

                        La contraseña no se volverá a mostrar
                        automáticamente después de esta operación.

                    </div>
                    '''
                )
            )

        # ====================================================
        # LIMPIAR VARIABLES TEMPORALES
        # ====================================================

        self._generated_password = None

        self._generated_username = None

        self._credentials_reason = None


# ============================================================
# REGISTRO DEL USUARIO
# ============================================================

admin.site.register(
    User,
    CustomUserAdmin
)


# ============================================================
# ADMINISTRACIÓN DE TUTORES
# ============================================================

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):

    list_display = [
        'nombre',
        'alumno',
        'parentesco',
        'telefono',
        'codigo_acceso',
    ]

    search_fields = [
        'nombre',
        'alumno__first_name',
        'alumno__last_name',
        'codigo_acceso',
    ]

    readonly_fields = [
        'codigo_acceso',
    ]

    list_filter = [
        'parentesco',
    ]