# bidii_builders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer-register/', views.customer_register, name='customer_register'),
    path('customer-profile/', views.customer_profile, name='customer_profile'),
    path('customer-estimates/', views.customer_estimates, name='customer_estimates'),
    path('customer-jobs/', views.customer_jobs, name='customer_jobs'),
    path('customer-invoices/', views.customer_invoices, name='customer_invoices'),
    
    # Customer CRUD
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Property CRUD
    path('properties/', views.property_list, name='property_list'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
    path('properties/<int:pk>/edit/', views.property_update, name='property_update'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),
    
    # Estimate CRUD
    path('estimates/', views.estimate_list, name='estimate_list'),
    path('estimates/create/', views.estimate_create, name='estimate_create'),
    path('estimates/<int:pk>/', views.estimate_detail, name='estimate_detail'),
    path('estimates/<int:pk>/edit/', views.estimate_update, name='estimate_update'),
    path('estimates/<int:pk>/delete/', views.estimate_delete, name='estimate_delete'),
    
    # Job CRUD
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_update, name='job_update'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    
    # Material CRUD
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/', views.material_detail, name='material_detail'),
    path('materials/<int:pk>/edit/', views.material_update, name='material_update'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    
    # Job Material CRUD
    path('job-materials/', views.job_material_list, name='job_material_list'),
    path('job-materials/create/', views.job_material_create, name='job_material_create'),
    path('job-materials/<int:pk>/', views.job_material_detail, name='job_material_detail'),
    path('job-materials/<int:pk>/edit/', views.job_material_update, name='job_material_update'),
    path('job-materials/<int:pk>/delete/', views.job_material_delete, name='job_material_delete'),
    
    # Invoice CRUD
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    
    # Payment CRUD
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    
    # AJAX endpoints
    path('api/properties/<int:customer_id>/', views.load_properties, name='load_properties'),
    path('api/create-property/', views.create_property_ajax, name='create_property_ajax'),
    
    # Jobs schedule (existing)
    path('jobs/schedule/', views.job_schedule, name='job_schedule'),
    path('jobs/<int:job_id>/add-material/', views.job_materials_add, name='job_materials_add'),
    
    # Reports and backup
    path('reports/', views.reports, name='reports'),
    path('backup/', views.backup, name='backup'),
    path('api/charts-data/', views.dashboard_charts_data, name='charts_data'),
]