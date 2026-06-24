# web/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Tutor

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'plantel', 'estatus', 'is_staff')
    list_filter = ('rol', 'plantel', 'estatus')
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información de FRAY', {
            'fields': ('rol', 'plantel', 'telefono', 'status')
        }),
    )
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

admin.site.register(User, CustomUserAdmin)

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'alumno', 'parentesco', 'telefono', 'codigo_acceso']
    search_fields = ['nombre', 'alumno__first_name', 'alumno__last_name', 'codigo_acceso']
    readonly_fields = ['codigo_acceso']
