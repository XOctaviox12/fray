# web/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'plantel', 'status', 'is_staff')
    list_filter = ('rol', 'plantel', 'status')
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información de FRAY', {
            'fields': ('rol', 'plantel', 'telefono', 'status')
        }),
    )
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

admin.site.register(User, CustomUserAdmin)