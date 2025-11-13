# bidii_builders/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Property(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.TextField()
    property_type = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.address[:50]}"

class Estimate(models.Model):
    ESTIMATE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    property_obj = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)  # Make nullable
    visit_date = models.DateField()
    initial_outline = models.TextField()
    detailed_estimate = models.TextField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=ESTIMATE_STATUS_CHOICES, default='pending')
    estimate_date = models.DateField(auto_now_add=True)
    sent_date = models.DateField(null=True, blank=True)
    accepted_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Estimate #{self.id} - {self.customer.full_name}"

class Job(models.Model):
    JOB_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='scheduled')
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job #{self.id} - {self.estimate.customer.full_name}"

class Material(models.Model):
    name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    supplier = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.unit})"

class JobMaterial(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Invoice(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.job.estimate.customer.full_name}"

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Payment for Invoice #{self.invoice.id}"