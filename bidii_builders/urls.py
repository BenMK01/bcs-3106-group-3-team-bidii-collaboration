# bidii_builders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('estimates/create/', views.estimate_create, name='estimate_create'),
    path('estimates/<int:pk>/', views.estimate_detail, name='estimate_detail'),
    path('jobs/schedule/', views.job_schedule, name='job_schedule'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('invoices/create/<int:job_id>/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('api/charts-data/', views.dashboard_charts_data, name='charts_data'),
]