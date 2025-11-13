# bidii_builders/forms.py
from django import forms
from .models import Customer, Property, Estimate, Job, Material, JobMaterial, Invoice


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "email", "phone", "address"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["address", "property_type", "description"]
        widgets = {
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "property_type": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = ["visit_date", "initial_outline", "detailed_estimate", "total_cost"]
        widgets = {
            "visit_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "initial_outline": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "detailed_estimate": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "total_cost": forms.NumberInput(attrs={"class": "form-control"}),
        }


class JobScheduleForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["scheduled_date", "start_date"]
        widgets = {
            "scheduled_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
