# bidii_builders/admin.py
from django.contrib import admin
from .models import Customer, Property, Estimate, Job, Material, JobMaterial, Invoice, Payment

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'address', 'property_type']
    list_filter = ['property_type']

@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'property_obj', 'total_cost', 'status', 'estimate_date']
    list_filter = ['status', 'estimate_date']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'estimate', 'start_date', 'status', 'scheduled_date']
    list_filter = ['status', 'start_date']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'job', 'amount', 'issue_date', 'is_paid']
    list_filter = ['is_paid', 'issue_date']