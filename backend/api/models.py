from django.db import models
import uuid

# Create your models here.
class FileUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False)
    file = models.FileField(upload_to='uploads/')
    filename = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10) # 'csv' or 'excel'

    def __str__(self):
        return f"{self.filename} - {self.upload_date}"
    
class ProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('processing','Processing'),
        ('completed','Completed'),
        ('failed','Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE)
    natural_language_query = models.TextField()
    generated_regex = models.TextField(blank=True)
    replacement_value = models.TextField()
    target_column = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Job {self.id} - {self.status}"