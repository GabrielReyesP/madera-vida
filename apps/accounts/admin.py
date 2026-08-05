"""
apps/accounts/admin.py
Registro de modelos de accounts en el panel de administración.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, WorkerProfile, CustomerProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('role', 'phone')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rut', 'position', 'hire_date')
    search_fields = ('user__username', 'rut', 'position')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rut', 'region')
    search_fields = ('user__username', 'rut')
