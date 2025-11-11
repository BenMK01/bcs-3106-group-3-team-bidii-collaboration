# bidii_builders/dashboard_visualization.py
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from django.db.models import Sum
from datetime import datetime, timedelta
from .models import Invoice, Job

def create_revenue_chart():
    """Create a revenue chart for the dashboard"""
    # Get revenue data for the last 12 months
    months = []
    revenues = []
    
    for i in range(12):
        month = datetime.now().replace(month=i+1) if i+1 <= datetime.now().month else datetime.now().replace(year=datetime.now().year-1, month=i+1)
        revenue = Invoice.objects.filter(
            issue_date__month=month.month,
            issue_date__year=month.year,
            is_paid=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        months.append(month.strftime('%b'))
        revenues.append(float(revenue))
    
    plt.figure(figsize=(12, 6))
    plt.bar(months, revenues)
    plt.title('Monthly Revenue')
    plt.xlabel('Month')
    plt.ylabel('Revenue (KES)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    
    plt.close()  # Close the figure to free memory
    
    return graphic

def create_job_status_chart():
    """Create a job status distribution chart"""
    from .models import Job
    
    status_counts = {}
    for status, label in Job.JOB_STATUS_CHOICES:
        count = Job.objects.filter(status=status).count()
        if count > 0:
            status_counts[label] = count
    
    if not status_counts:
        return None
    
    plt.figure(figsize=(8, 8))
    plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
    plt.title('Job Status Distribution')
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    
    plt.close()  # Close the figure to free memory
    
    return graphic