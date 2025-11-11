# bidii_builders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from .models import Customer, Property, Estimate, Job, Material, JobMaterial, Invoice, Payment
from django.http import JsonResponse
import json

def dashboard(request):
    # Dashboard statistics
    total_customers = Customer.objects.count()
    pending_estimates = Estimate.objects.filter(status='pending').count()
    accepted_estimates = Estimate.objects.filter(status='accepted').count()
    active_jobs = Job.objects.filter(status='in_progress').count()
    completed_jobs = Job.objects.filter(status='completed').count()
    
    # Revenue statistics
    total_revenue = Invoice.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    overdue_invoices = Invoice.objects.filter(due_date__lt=datetime.now().date(), is_paid=False).count()
    
    # Recent activities
    recent_customers = Customer.objects.order_by('-created_at')[:5]
    recent_jobs = Job.objects.order_by('-created_at')[:5]
    
    context = {
        'total_customers': total_customers,
        'pending_estimates': pending_estimates,
        'accepted_estimates': accepted_estimates,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'total_revenue': total_revenue,
        'overdue_invoices': overdue_invoices,
        'recent_customers': recent_customers,
        'recent_jobs': recent_jobs,
    }
    return render(request, 'bidii_builders/dashboard.html', context)

def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'bidii_builders/customers/list.html', {'customers': customers})

def customer_create(request):
    if request.method == 'POST':
        # Create customer logic
        customer = Customer.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address')
        )
        messages.success(request, 'Customer created successfully!')
        return redirect('customer_detail', pk=customer.id)
    return render(request, 'bidii_builders/customers/create.html')

def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    properties = Property.objects.filter(customer=customer)
    estimates = Estimate.objects.filter(customer=customer)
    jobs = Job.objects.filter(estimate__customer=customer)
    invoices = Invoice.objects.filter(job__estimate__customer=customer)
    
    context = {
        'customer': customer,
        'properties': properties,
        'estimates': estimates,
        'jobs': jobs,
        'invoices': invoices,
    }
    return render(request, 'bidii_builders/customers/detail.html', context)

def estimate_create(request):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST.get('customer_id'))
        property_obj = get_object_or_404(Property, pk=request.POST.get('property_id'))
        
        estimate = Estimate.objects.create(
            customer=customer,
            property_obj=property_obj,
            visit_date=request.POST.get('visit_date'),
            initial_outline=request.POST.get('initial_outline'),
            detailed_estimate=request.POST.get('detailed_estimate'),
            total_cost=request.POST.get('total_cost'),
            status='pending'
        )
        messages.success(request, 'Estimate created successfully!')
        return redirect('estimate_detail', pk=estimate.id)
    
    customers = Customer.objects.all()
    return render(request, 'bidii_builders/estimates/create.html', {'customers': customers})

def estimate_detail(request, pk):
    estimate = get_object_or_404(Estimate, pk=pk)
    return render(request, 'bidii_builders/estimates/detail.html', {'estimate': estimate})

def job_schedule(request):
    if request.method == 'POST':
        estimate = get_object_or_404(Estimate, pk=request.POST.get('estimate_id'), status='accepted')
        
        job = Job.objects.create(
            estimate=estimate,
            start_date=request.POST.get('start_date'),
            scheduled_date=request.POST.get('scheduled_date'),
            status='scheduled'
        )
        messages.success(request, 'Job scheduled successfully!')
        return redirect('job_detail', pk=job.id)
    
    accepted_estimates = Estimate.objects.filter(status='accepted')
    return render(request, 'bidii_builders/jobs/schedule.html', {'estimates': accepted_estimates})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    materials = JobMaterial.objects.filter(job=job)
    invoice = Invoice.objects.filter(job=job).first()
    
    context = {
        'job': job,
        'materials': materials,
        'invoice': invoice
    }
    return render(request, 'bidii_builders/jobs/detail.html', context)

def invoice_create(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    
    if request.method == 'POST':
        # Calculate actual cost based on materials and labor
        materials_cost = JobMaterial.objects.filter(job=job).aggregate(Sum('total_price'))['total_price__sum'] or 0
        actual_cost = materials_cost  # Add labor costs if needed
        
        invoice = Invoice.objects.create(
            job=job,
            amount=actual_cost,
            due_date=datetime.now().date() + timedelta(days=30)
        )
        job.status = 'completed'
        job.actual_cost = actual_cost
        job.save()
        
        messages.success(request, 'Invoice created successfully!')
        return redirect('invoice_detail', pk=invoice.id)
    
    materials_cost = JobMaterial.objects.filter(job=job).aggregate(Sum('total_price'))['total_price__sum'] or 0
    context = {
        'job': job,
        'materials_cost': materials_cost
    }
    return render(request, 'bidii_builders/invoices/create.html', context)

def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = Payment.objects.filter(invoice=invoice)
    
    context = {
        'invoice': invoice,
        'payments': payments
    }
    return render(request, 'bidii_builders/invoices/detail.html', context)

def dashboard_charts_data(request):
    """API endpoint for chart data"""
    # Revenue by month
    revenue_data = []
    for i in range(12):
        month = datetime.now().date().replace(month=i+1) if i+1 <= datetime.now().month else datetime.now().date().replace(year=datetime.now().year-1, month=i+1)
        revenue = Invoice.objects.filter(
            issue_date__month=month.month,
            issue_date__year=month.year,
            is_paid=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_data.append({
            'month': month.strftime('%B'),
            'revenue': float(revenue)
        })
    
    # Job status distribution
    job_status_data = []
    for status, label in Job.JOB_STATUS_CHOICES:
        count = Job.objects.filter(status=status).count()
        job_status_data.append({'status': label, 'count': count})
    
    data = {
        'revenue_data': revenue_data,
        'job_status_data': job_status_data
    }
    return JsonResponse(data)