# bidii_builders/tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date
from .models import Customer, Property, Estimate, Job, Material, JobMaterial, Invoice, Payment

class CustomerModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )

    def test_customer_creation(self):
        """Test customer model creation"""
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.last_name, 'Doe')
        self.assertEqual(self.customer.email, 'john@example.com')
        self.assertEqual(self.customer.full_name, 'John Doe')

    def test_customer_string_representation(self):
        """Test customer string representation"""
        expected_str = f"{self.customer.first_name} {self.customer.last_name}"
        self.assertEqual(str(self.customer), expected_str)

class EstimateModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )
        self.property = Property.objects.create(
            customer=self.customer,
            address='456 Oak Ave',
            property_type='House',
            description='Residential property'
        )

    def test_estimate_creation(self):
        """Test estimate model creation"""
        estimate = Estimate.objects.create(
            customer=self.customer,
            property_obj=self.property,
            visit_date=date.today(),
            initial_outline='Initial work',
            detailed_estimate='Detailed estimate',
            total_cost=Decimal('50000.00'),
            status='pending'
        )
        
        self.assertEqual(estimate.customer, self.customer)
        self.assertEqual(estimate.property_obj, self.property)
        self.assertEqual(estimate.total_cost, Decimal('50000.00'))
        self.assertEqual(estimate.status, 'pending')
        self.assertEqual(str(estimate), f"Estimate #{estimate.id} - {self.customer.full_name}")

class EstimateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )
        self.property = Property.objects.create(
            customer=self.customer,
            address='456 Oak Ave',
            property_type='House',
            description='Residential property'
        )

    def test_estimate_list_view(self):
        """Test estimate list view requires authentication"""
        response = self.client.get(reverse('estimate_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and test
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('estimate_list'))
        self.assertEqual(response.status_code, 200)

    def test_estimate_create_view(self):
        """Test estimate creation view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('estimate_create'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        post_data = {
            'customer': self.customer.id,
            'property_obj': self.property.id,
            'visit_date': '2023-12-01',
            'initial_outline': 'Initial work',
            'detailed_estimate': 'Detailed estimate',
            'total_cost': '50000.00',
            'status': 'pending'
        }
        response = self.client.post(reverse('estimate_create'), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify estimate was created
        self.assertEqual(Estimate.objects.count(), 1)
        estimate = Estimate.objects.first()
        self.assertEqual(estimate.customer, self.customer)
        self.assertEqual(estimate.total_cost, Decimal('50000.00'))

class CustomerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )

    def test_customer_list_view(self):
        """Test customer list view"""
        response = self.client.get(reverse('customer_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and test
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_customer_create_view(self):
        """Test customer creation view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('customer_create'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        post_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'phone': '0987654321',
            'address': '789 Pine St'
        }
        response = self.client.post(reverse('customer_create'), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify customer was created
        self.assertEqual(Customer.objects.count(), 2)
        customer = Customer.objects.get(email='jane@example.com')
        self.assertEqual(customer.first_name, 'Jane')

class APIViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )

    def test_load_properties_api(self):
        """Test load properties API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        property1 = Property.objects.create(
            customer=self.customer,
            address='456 Oak Ave',
            property_type='House',
            description='Residential property'
        )
        
        response = self.client.get(f'/api/properties/{self.customer.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            [{'id': property1.id, 'address': '456 Oak Ave'}]
        )

    def test_create_property_api(self):
        """Test create property API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        post_data = {
            'customer_id': self.customer.id,
            'address': '789 Elm St',
            'property_type': 'Apartment'
        }
        
        response = self.client.post(
            '/api/create-property/',
            content_type='application/json',
            data=post_data
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify property was created
        self.assertEqual(Property.objects.count(), 1)
        property_obj = Property.objects.first()
        self.assertEqual(property_obj.address, '789 Elm St')

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )

    def test_admin_required_for_estimate_list(self):
        """Test that admin access is required for estimate list"""
        response = self.client.get(reverse('estimate_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login as regular user (not staff)
        regular_user = User.objects.create_user(
            username='regularuser',
            password='regularpass'
        )
        self.client.login(username='regularuser', password='regularpass')
        response = self.client.get(reverse('estimate_list'))
        self.assertEqual(response.status_code, 302)  # Should redirect to customer dashboard
        
        # Login as staff user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('estimate_list'))
        self.assertEqual(response.status_code, 200)  # Should allow access

class BusinessLogicTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St'
        )
        self.property = Property.objects.create(
            customer=self.customer,
            address='456 Oak Ave',
            property_type='House',
            description='Residential property'
        )

    def test_estimate_workflow(self):
        """Test complete estimate workflow"""
        # Create estimate
        estimate = Estimate.objects.create(
            customer=self.customer,
            property_obj=self.property,
            visit_date=date.today(),
            initial_outline='Initial work',
            detailed_estimate='Detailed estimate',
            total_cost=Decimal('50000.00'),
            status='pending'
        )
        
        # Accept estimate
        estimate.status = 'accepted'
        estimate.save()
        
        # Create job from accepted estimate
        job = Job.objects.create(
            estimate=estimate,
            start_date=date.today(),
            scheduled_date=date.today(),
            status='scheduled'
        )
        
        # Verify workflow
        self.assertEqual(estimate.status, 'accepted')
        self.assertEqual(job.estimate, estimate)
        self.assertEqual(job.status, 'scheduled')

    def test_invoice_creation_from_job(self):
        """Test invoice creation from completed job"""
        estimate = Estimate.objects.create(
            customer=self.customer,
            property_obj=self.property,
            visit_date=date.today(),
            initial_outline='Initial work',
            detailed_estimate='Detailed estimate',
            total_cost=Decimal('50000.00'),
            status='accepted'
        )
        
        job = Job.objects.create(
            estimate=estimate,
            start_date=date.today(),
            scheduled_date=date.today(),
            status='completed',
            actual_cost=Decimal('48000.00')
        )
        
        invoice = Invoice.objects.create(
            job=job,
            amount=Decimal('48000.00'),
            due_date=date.today()
        )
        
        # Verify invoice is linked to job and estimate
        self.assertEqual(invoice.job, job)
        self.assertEqual(invoice.job.estimate, estimate)
        self.assertEqual(invoice.amount, Decimal('48000.00'))