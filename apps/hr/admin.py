"""
apps/hr/admin.py
"""

from django.contrib import admin

from .models import OvertimeRecord, PayrollAdjustment, PayrollRecord


@admin.register(OvertimeRecord)
class OvertimeRecordAdmin(admin.ModelAdmin):
    list_display = ('worker', 'date', 'hours', 'total', 'status')
    list_filter = ('status',)
    search_fields = ('worker__user__email', 'worker__rut')
    readonly_fields = ('hourly_rate', 'overtime_rate', 'total')


@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('worker', 'adjustment_type', 'amount', 'period')
    list_filter = ('adjustment_type',)
    search_fields = ('worker__user__email', 'worker__rut')


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('worker', 'period', 'taxable_income', 'net_pay', 'status')
    list_filter = ('status',)
    search_fields = ('worker__user__email', 'worker__rut')
    readonly_fields = (
        'base_salary', 'overtime_total', 'bonuses_total', 'taxable_income',
        'afp_name', 'afp_percentage', 'afp_amount', 'health_amount',
        'advances_total', 'deductions_total', 'net_pay', 'created_at',
    )
