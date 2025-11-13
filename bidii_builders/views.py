# bidii_builders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from .models import Customer, Property, Estimate, Job, Material, JobMaterial, Invoice, Payment
from django.http import JsonResponse, HttpResponse, Http404
import json
import os
import zipfile
from django.conf import settings

def index(request):
    """Main index view that redirects to appropriate dashboard"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard')
        else:
            # Check if user is linked to a customer profile
            try:
                customer = Customer.objects.get(user=request.user)
                return redirect('customer_dashboard')
            except Customer.DoesNotExist:
                # If user exists but no customer profile, show login again
                messages.warning(request, 'Your account is not linked to a customer profile. Please contact support.')
                return redirect('login')
    else:
        return redirect('login')

@login_required
def dashboard(request):
    """Admin dashboard - only accessible to staff"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
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

@login_required
def customer_dashboard(request):
    """Customer dashboard - only accessible to customers"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Your account is not linked to a customer profile. Please contact support.')
        return redirect('login')
    
    # Customer-specific statistics
    total_estimates = Estimate.objects.filter(customer=customer).count()
    pending_estimates = Estimate.objects.filter(customer=customer, status='pending').count()
    accepted_estimates = Estimate.objects.filter(customer=customer, status='accepted').count()
    active_jobs = Job.objects.filter(estimate__customer=customer, status='in_progress').count()
    completed_jobs = Job.objects.filter(estimate__customer=customer, status='completed').count()
    
    # Recent activities for this customer
    recent_estimates = Estimate.objects.filter(customer=customer).order_by('-created_at')[:5]
    recent_jobs = Job.objects.filter(estimate__customer=customer).order_by('-created_at')[:5]
    
    context = {
        'customer': customer,
        'total_estimates': total_estimates,
        'pending_estimates': pending_estimates,
        'accepted_estimates': accepted_estimates,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'recent_estimates': recent_estimates,
        'recent_jobs': recent_jobs,
    }
    return render(request, 'bidii_builders/customer_dashboard.html', context)

# Customer CRUD Operations
@login_required
def customer_list(request):
    """Admin view - list all customers"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    query = request.GET.get('q')
    if query:
        customers = Customer.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    else:
        customers = Customer.objects.all()
    
    return render(request, 'bidii_builders/customers/list.html', {'customers': customers})

@login_required
def customer_create(request):
    """Admin create customer"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    if request.method == 'POST':
        # Create customer logic
        customer = Customer.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address')
        )
        
        # Optionally create a user account for the customer
        if request.POST.get('create_user_account'):
            username = request.POST.get('email')  # Use email as username
            password = request.POST.get('password', 'defaultpassword123')  # Allow custom password
            
            # Check if user already exists
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=username,
                    password=password
                )
                customer.user = user
                customer.save()
                messages.success(request, f'Customer created with user account: {username}')
            else:
                messages.warning(request, 'User account already exists for this email')
        
        messages.success(request, 'Customer created successfully!')
        return redirect('customer_detail', pk=customer.id)
    return render(request, 'bidii_builders/customers/create.html')

@login_required
def customer_detail(request, pk):
    """Admin view customer details"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
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

@login_required
def customer_update(request, pk):
    """Admin update customer"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.first_name = request.POST.get('first_name')
        customer.last_name = request.POST.get('last_name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')
        customer.save()
        
        messages.success(request, 'Customer updated successfully!')
        return redirect('customer_detail', pk=customer.id)
    
    return render(request, 'bidii_builders/customers/update.html', {'customer': customer})

@login_required
def customer_delete(request, pk):
    """Admin delete customer"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('customer_list')
    
    return render(request, 'bidii_builders/customers/delete.html', {'customer': customer})

# Property CRUD Operations
@login_required
def property_list(request):
    """List all properties - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    properties = Property.objects.all()
    return render(request, 'bidii_builders/properties/list.html', {'properties': properties})

@login_required
def property_create(request):
    """Create property - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    customers = Customer.objects.all()
    
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'))
        property_obj = Property.objects.create(
            customer=customer,
            address=request.POST.get('address'),
            property_type=request.POST.get('property_type'),
            description=request.POST.get('description')
        )
        messages.success(request, 'Property created successfully!')
        return redirect('property_detail', pk=property_obj.id)
    
    return render(request, 'bidii_builders/properties/create.html', {'customers': customers})

@login_required
def property_detail(request, pk):
    """View property detail - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    property_obj = get_object_or_404(Property, pk=pk)
    return render(request, 'bidii_builders/properties/detail.html', {'property': property_obj})

@login_required
def property_update(request, pk):
    """Update property - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    property_obj = get_object_or_404(Property, pk=pk)
    customers = Customer.objects.all()
    
    if request.method == 'POST':
        property_obj.customer = get_object_or_404(Customer, pk=request.POST.get('customer'))
        property_obj.address = request.POST.get('address')
        property_obj.property_type = request.POST.get('property_type')
        property_obj.description = request.POST.get('description')
        property_obj.save()
        
        messages.success(request, 'Property updated successfully!')
        return redirect('property_detail', pk=property_obj.id)
    
    return render(request, 'bidii_builders/properties/update.html', {
        'property': property_obj,
        'customers': customers
    })

@login_required
def property_delete(request, pk):
    """Delete property - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    property_obj = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('property_list')
    
    return render(request, 'bidii_builders/properties/delete.html', {'property': property_obj})

# Estimate CRUD Operations
@login_required
def estimate_list(request):
    """List all estimates - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    estimates = Estimate.objects.all()
    return render(request, 'bidii_builders/estimates/list.html', {'estimates': estimates})

@login_required
def estimate_create(request):
    """Create estimate - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    customers = Customer.objects.all()
    properties = Property.objects.all()
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        
        # Validate customer
        if not customer_id or customer_id == '':
            messages.error(request, 'Please select a customer.')
            return render(request, 'bidii_builders/estimates/create.html', {
                'customers': customers,
                'properties': properties
            })
        
        customer = get_object_or_404(Customer, pk=int(customer_id))
        
        # Property is now optional
        property_id = request.POST.get('property_obj')
        property_obj = None
        
        if property_id and property_id != '':
            property_obj = get_object_or_404(Property, pk=int(property_id))
        
        estimate = Estimate.objects.create(
            customer=customer,
            property_obj=property_obj,  # Can be None
            visit_date=request.POST.get('visit_date'),
            initial_outline=request.POST.get('initial_outline'),
            detailed_estimate=request.POST.get('detailed_estimate'),
            total_cost=request.POST.get('total_cost'),
            status=request.POST.get('status', 'pending')
        )
        messages.success(request, 'Estimate created successfully!')
        return redirect('estimate_detail', pk=estimate.id)
    
    return render(request, 'bidii_builders/estimates/create.html', {
        'customers': customers,
        'properties': properties
    })

@login_required
def estimate_detail(request, pk):
    """View estimate detail - accessible to both staff and customer"""
    estimate = get_object_or_404(Estimate, pk=pk)
    
    # Check if user has permission to view this estimate
    if not request.user.is_staff:
        try:
            customer = Customer.objects.get(user=request.user)
            if estimate.customer != customer:
                messages.error(request, 'You do not have permission to view this estimate.')
                return redirect('customer_dashboard')
        except Customer.DoesNotExist:
            messages.error(request, 'You need to be linked to a customer profile to view this estimate.')
            return redirect('login')
    
    return render(request, 'bidii_builders/estimates/detail.html', {'estimate': estimate})

@login_required
def estimate_update(request, pk):
    """Update estimate - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    estimate = get_object_or_404(Estimate, pk=pk)
    customers = Customer.objects.all()
    properties = Property.objects.filter(customer=estimate.customer)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        
        # Validate customer
        if not customer_id or customer_id == '':
            messages.error(request, 'Please select a customer.')
            return render(request, 'bidii_builders/estimates/update.html', {
                'estimate': estimate,
                'customers': customers,
                'properties': properties
            })
        
        customer = get_object_or_404(Customer, pk=int(customer_id))
        
        # Property is now optional
        property_id = request.POST.get('property_obj')
        property_obj = None
        
        if property_id and property_id != '':
            property_obj = get_object_or_404(Property, pk=int(property_id))
        
        estimate.customer = customer
        estimate.property_obj = property_obj  # Can be None
        estimate.visit_date = request.POST.get('visit_date')
        estimate.initial_outline = request.POST.get('initial_outline')
        estimate.detailed_estimate = request.POST.get('detailed_estimate')
        estimate.total_cost = request.POST.get('total_cost')
        estimate.status = request.POST.get('status', 'pending')
        estimate.save()
        
        messages.success(request, 'Estimate updated successfully!')
        return redirect('estimate_detail', pk=estimate.id)
    
    return render(request, 'bidii_builders/estimates/update.html', {
        'estimate': estimate,
        'customers': customers,
        'properties': properties
    })

@login_required
def estimate_delete(request, pk):
    """Delete estimate - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    estimate = get_object_or_404(Estimate, pk=pk)
    
    if request.method == 'POST':
        estimate.delete()
        messages.success(request, 'Estimate deleted successfully!')
        return redirect('estimate_list')
    
    return render(request, 'bidii_builders/estimates/delete.html', {'estimate': estimate})

# Job CRUD Operations
@login_required
def job_list(request):
    """List all jobs - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    jobs = Job.objects.all()
    return render(request, 'bidii_builders/jobs/list.html', {'jobs': jobs})

@login_required
def job_create(request):
    """Create job - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    estimates = Estimate.objects.filter(status='accepted')
    
    if request.method == 'POST':
        estimate = get_object_or_404(Estimate, pk=request.POST.get('estimate'))
        
        job = Job.objects.create(
            estimate=estimate,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            scheduled_date=request.POST.get('scheduled_date'),
            status=request.POST.get('status', 'scheduled'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Job created successfully!')
        return redirect('job_detail', pk=job.id)
    
    return render(request, 'bidii_builders/jobs/create.html', {'estimates': estimates})

@login_required
def job_detail(request, pk):
    """View job detail - accessible to both staff and customer"""
    job = get_object_or_404(Job, pk=pk)
    
    # Check if user has permission to view this job
    if not request.user.is_staff:
        try:
            customer = Customer.objects.get(user=request.user)
            if job.estimate.customer != customer:
                messages.error(request, 'You do not have permission to view this job.')
                return redirect('customer_dashboard')
        except Customer.DoesNotExist:
            messages.error(request, 'You need to be linked to a customer profile to view this job.')
            return redirect('login')
    
    materials = JobMaterial.objects.filter(job=job)
    invoice = Invoice.objects.filter(job=job).first()
    
    context = {
        'job': job,
        'materials': materials,
        'invoice': invoice
    }
    return render(request, 'bidii_builders/jobs/detail.html', context)

@login_required
def job_update(request, pk):
    """Update job - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job = get_object_or_404(Job, pk=pk)
    estimates = Estimate.objects.all()
    
    if request.method == 'POST':
        job.estimate = get_object_or_404(Estimate, pk=request.POST.get('estimate'))
        job.start_date = request.POST.get('start_date')
        job.end_date = request.POST.get('end_date')
        job.scheduled_date = request.POST.get('scheduled_date')
        job.status = request.POST.get('status', 'scheduled')
        job.notes = request.POST.get('notes', '')
        job.save()
        
        messages.success(request, 'Job updated successfully!')
        return redirect('job_detail', pk=job.id)
    
    return render(request, 'bidii_builders/jobs/update.html', {
        'job': job,
        'estimates': estimates
    })

@login_required
def job_delete(request, pk):
    """Delete job - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job = get_object_or_404(Job, pk=pk)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('job_list')
    
    return render(request, 'bidii_builders/jobs/delete.html', {'job': job})

# Material CRUD Operations
@login_required
def material_list(request):
    """List all materials - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    materials = Material.objects.all()
    return render(request, 'bidii_builders/materials/list.html', {'materials': materials})

@login_required
def material_create(request):
    """Create material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    if request.method == 'POST':
        material = Material.objects.create(
            name=request.POST.get('name'),
            unit_price=request.POST.get('unit_price'),
            unit=request.POST.get('unit'),
            supplier=request.POST.get('supplier')
        )
        messages.success(request, 'Material created successfully!')
        return redirect('material_detail', pk=material.id)
    
    return render(request, 'bidii_builders/materials/create.html')

@login_required
def material_detail(request, pk):
    """View material detail - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    material = get_object_or_404(Material, pk=pk)
    return render(request, 'bidii_builders/materials/detail.html', {'material': material})

@login_required
def material_update(request, pk):
    """Update material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        material.name = request.POST.get('name')
        material.unit_price = request.POST.get('unit_price')
        material.unit = request.POST.get('unit')
        material.supplier = request.POST.get('supplier')
        material.save()
        
        messages.success(request, 'Material updated successfully!')
        return redirect('material_detail', pk=material.id)
    
    return render(request, 'bidii_builders/materials/update.html', {'material': material})

@login_required
def material_delete(request, pk):
    """Delete material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    material = get_object_or_404(Material, pk=pk)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material deleted successfully!')
        return redirect('material_list')
    
    return render(request, 'bidii_builders/materials/delete.html', {'material': material})

# Job Material CRUD Operations
@login_required
def job_material_list(request):
    """List all job materials - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job_materials = JobMaterial.objects.all()
    return render(request, 'bidii_builders/job_materials/list.html', {'job_materials': job_materials})

@login_required
def job_material_create(request):
    """Create job material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    jobs = Job.objects.all()
    materials = Material.objects.all()
    
    if request.method == 'POST':
        job = get_object_or_404(Job, pk=request.POST.get('job'))
        material = get_object_or_404(Material, pk=request.POST.get('material'))
        
        job_material = JobMaterial.objects.create(
            job=job,
            material=material,
            quantity=request.POST.get('quantity'),
            unit_price=request.POST.get('unit_price')
        )
        messages.success(request, 'Job material created successfully!')
        return redirect('job_material_detail', pk=job_material.id)
    
    return render(request, 'bidii_builders/job_materials/create.html', {
        'jobs': jobs,
        'materials': materials
    })

@login_required
def job_material_detail(request, pk):
    """View job material detail - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job_material = get_object_or_404(JobMaterial, pk=pk)
    return render(request, 'bidii_builders/job_materials/detail.html', {'job_material': job_material})

@login_required
def job_material_update(request, pk):
    """Update job material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job_material = get_object_or_404(JobMaterial, pk=pk)
    jobs = Job.objects.all()
    materials = Material.objects.all()
    
    if request.method == 'POST':
        job_material.job = get_object_or_404(Job, pk=request.POST.get('job'))
        job_material.material = get_object_or_404(Material, pk=request.POST.get('material'))
        job_material.quantity = request.POST.get('quantity')
        job_material.unit_price = request.POST.get('unit_price')
        job_material.save()
        
        messages.success(request, 'Job material updated successfully!')
        return redirect('job_material_detail', pk=job_material.id)
    
    return render(request, 'bidii_builders/job_materials/update.html', {
        'job_material': job_material,
        'jobs': jobs,
        'materials': materials
    })

@login_required
def job_material_delete(request, pk):
    """Delete job material - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job_material = get_object_or_404(JobMaterial, pk=pk)
    
    if request.method == 'POST':
        job_material.delete()
        messages.success(request, 'Job material deleted successfully!')
        return redirect('job_material_list')
    
    return render(request, 'bidii_builders/job_materials/delete.html', {'job_material': job_material})

# Invoice CRUD Operations
@login_required
def invoice_list(request):
    """List all invoices - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    invoices = Invoice.objects.all()
    return render(request, 'bidii_builders/invoices/list.html', {'invoices': invoices})

@login_required
def invoice_create(request, job_id=None):
    """Create invoice - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    jobs = Job.objects.filter(status='completed')  # Only completed jobs can have invoices
    
    if job_id:
        job = get_object_or_404(Job, pk=job_id)
    else:
        job = None
    
    if request.method == 'POST':
        job = get_object_or_404(Job, pk=request.POST.get('job'))
        
        invoice = Invoice.objects.create(
            job=job,
            amount=request.POST.get('amount'),
            due_date=request.POST.get('due_date'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Invoice created successfully!')
        return redirect('invoice_detail', pk=invoice.id)
    
    return render(request, 'bidii_builders/invoices/create.html', {
        'jobs': jobs,
        'job': job
    })

@login_required
def invoice_detail(request, pk):
    """View invoice detail - accessible to both staff and customer"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Check if user has permission to view this invoice
    if not request.user.is_staff:
        try:
            customer = Customer.objects.get(user=request.user)
            if invoice.job.estimate.customer != customer:
                messages.error(request, 'You do not have permission to view this invoice.')
                return redirect('customer_dashboard')
        except Customer.DoesNotExist:
            messages.error(request, 'You need to be linked to a customer profile to view this invoice.')
            return redirect('login')
    
    payments = Payment.objects.filter(invoice=invoice)
    
    context = {
        'invoice': invoice,
        'payments': payments
    }
    return render(request, 'bidii_builders/invoices/detail.html', context)

@login_required
def invoice_update(request, pk):
    """Update invoice - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    invoice = get_object_or_404(Invoice, pk=pk)
    jobs = Job.objects.all()
    
    if request.method == 'POST':
        invoice.job = get_object_or_404(Job, pk=request.POST.get('job'))
        invoice.amount = request.POST.get('amount')
        invoice.due_date = request.POST.get('due_date')
        invoice.notes = request.POST.get('notes', '')
        invoice.save()
        
        messages.success(request, 'Invoice updated successfully!')
        return redirect('invoice_detail', pk=invoice.id)
    
    return render(request, 'bidii_builders/invoices/update.html', {
        'invoice': invoice,
        'jobs': jobs
    })

@login_required
def invoice_delete(request, pk):
    """Delete invoice - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('invoice_list')
    
    return render(request, 'bidii_builders/invoices/delete.html', {'invoice': invoice})

# Payment CRUD Operations
@login_required
def payment_list(request):
    """List all payments - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    payments = Payment.objects.all()
    return render(request, 'bidii_builders/payments/list.html', {'payments': payments})

@login_required
def payment_create(request):
    """Create payment - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    invoices = Invoice.objects.filter(is_paid=False)  # Only unpaid invoices can receive payments
    
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=request.POST.get('invoice'))
        
        payment = Payment.objects.create(
            invoice=invoice,
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('payment_method'),
            reference_number=request.POST.get('reference_number', '')
        )
        
        # Update invoice status if payment covers full amount
        if payment.amount >= invoice.amount:
            invoice.is_paid = True
            invoice.paid_date = datetime.now().date()
            invoice.save()
        
        messages.success(request, 'Payment created successfully!')
        return redirect('payment_detail', pk=payment.id)
    
    return render(request, 'bidii_builders/payments/create.html', {'invoices': invoices})

@login_required
def payment_detail(request, pk):
    """View payment detail - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'bidii_builders/payments/detail.html', {'payment': payment})

@login_required
def payment_update(request, pk):
    """Update payment - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    payment = get_object_or_404(Payment, pk=pk)
    invoices = Invoice.objects.all()
    
    if request.method == 'POST':
        payment.invoice = get_object_or_404(Invoice, pk=request.POST.get('invoice'))
        payment.amount = request.POST.get('amount')
        payment.payment_method = request.POST.get('payment_method')
        payment.reference_number = request.POST.get('reference_number', '')
        payment.save()
        
        messages.success(request, 'Payment updated successfully!')
        return redirect('payment_detail', pk=payment.id)
    
    return render(request, 'bidii_builders/payments/update.html', {
        'payment': payment,
        'invoices': invoices
    })

@login_required
def payment_delete(request, pk):
    """Delete payment - staff only"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    
    return render(request, 'bidii_builders/payments/delete.html', {'payment': payment})

# AJAX endpoints
@login_required
def load_properties(request, customer_id):
    """AJAX endpoint to load properties for a specific customer"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    properties = Property.objects.filter(customer_id=customer_id).values('id', 'address')
    return JsonResponse(list(properties), safe=False)

@login_required
def create_property_ajax(request):
    """AJAX endpoint to create a property"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_id = data.get('customer_id')
            address = data.get('address')
            property_type = data.get('property_type', 'House')
            
            if not customer_id or not address:
                return JsonResponse({'success': False, 'error': 'Customer ID and address are required'})
            
            customer = get_object_or_404(Customer, pk=int(customer_id))
            property_obj = Property.objects.create(
                customer=customer,
                address=address,
                property_type=property_type
            )
            
            return JsonResponse({
                'success': True,
                'property_id': property_obj.id,
                'address': property_obj.address
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Additional functions
@login_required
def job_schedule(request):
    """Admin schedule job"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
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

@login_required
def job_materials_add(request, job_id):
    """Admin add material to job"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    job = get_object_or_404(Job, pk=job_id)
    materials = Material.objects.all()
    
    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')
        material = get_object_or_404(Material, pk=material_id)
        
        JobMaterial.objects.create(
            job=job,
            material=material,
            quantity=quantity,
            unit_price=material.unit_price
        )
        messages.success(request, 'Material added to job successfully!')
        return redirect('job_detail', pk=job_id)
    
    return render(request, 'bidii_builders/job_materials/add.html', {
        'job': job,
        'materials': materials
    })

@login_required
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

@login_required
def reports(request):
    """Admin reports"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    # Monthly revenue report
    monthly_revenue = []
    for i in range(12):
        month = datetime.now().replace(month=i+1) if i+1 <= datetime.now().month else datetime.now().replace(year=datetime.now().year-1, month=i+1)
        revenue = Invoice.objects.filter(
            issue_date__month=month.month,
            issue_date__year=month.year,
            is_paid=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_revenue.append({
            'month': month.strftime('%B'),
            'revenue': float(revenue)
        })
    
    # Job status report
    job_status_counts = {}
    for status, label in Job.JOB_STATUS_CHOICES:
        count = Job.objects.filter(status=status).count()
        job_status_counts[label] = count
    
    context = {
        'monthly_revenue': monthly_revenue,
        'job_status_counts': job_status_counts,
        'total_customers': Customer.objects.count(),
        'total_jobs': Job.objects.count(),
        'total_revenue': Invoice.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    return render(request, 'bidii_builders/reports.html', context)

@login_required
def backup(request):
    """Admin backup"""
    if not request.user.is_staff:
        return redirect('customer_dashboard')
    
    import os
    from django.conf import settings
    from django.http import HttpResponse
    import zipfile
    from datetime import datetime
    
    if request.method == 'POST':
        # Create backup of database
        db_path = str(settings.BASE_DIR / 'db.sqlite3')
        backup_filename = f"bidii_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(backup_filename, 'w') as zipf:
            zipf.write(db_path, os.path.basename(db_path))
        
        with open(backup_filename, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={backup_filename}'
            
        os.remove(backup_filename)  # Clean up after download
        return response
    
    return render(request, 'bidii_builders/backup.html')

# Customer-specific views
@login_required
def customer_register(request):
    """Allow customers to register themselves"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'bidii_builders/customer_register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'bidii_builders/customer_register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create customer profile
        customer = Customer.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address
        )
        
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')
    
    return render(request, 'bidii_builders/customer_register.html')

@login_required
def customer_profile(request):
    """Customer profile page - only accessible to customers"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Your account is not linked to a customer profile.')
        return redirect('login')
    
    if request.method == 'POST':
        customer.first_name = request.POST.get('first_name')
        customer.last_name = request.POST.get('last_name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')
        customer.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('customer_profile')
    
    context = {
        'customer': customer
    }
    return render(request, 'bidii_builders/customer_profile.html', context)

@login_required
def customer_estimates(request):
    """Customer view of their estimates"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Your account is not linked to a customer profile.')
        return redirect('login')
    
    estimates = Estimate.objects.filter(customer=customer).order_by('-created_at')
    
    context = {
        'estimates': estimates
    }
    return render(request, 'bidii_builders/customer_estimates.html', context)

@login_required
def customer_jobs(request):
    """Customer view of their jobs"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Your account is not linked to a customer profile.')
        return redirect('login')
    
    jobs = Job.objects.filter(estimate__customer=customer).order_by('-created_at')
    
    context = {
        'jobs': jobs
    }
    return render(request, 'bidii_builders/customer_jobs.html', context)

@login_required
def customer_invoices(request):
    """Customer view of their invoices"""
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Your account is not linked to a customer profile.')
        return redirect('login')
    
    invoices = Invoice.objects.filter(job__estimate__customer=customer).order_by('-issue_date')
    
    context = {
        'invoices': invoices
    }
    return render(request, 'bidii_builders/customer_invoices.html', context)