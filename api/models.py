from django.db import models
import uuid
from admin_app.models import PaperWork

class Review(models.Model):
    STATUS_CHOICES = (
        ('ASSIGNED', 'Assigned'),
        ('SUBMITTED', 'Submitted'),
        ('CHANGES_REQUESTED', 'Changes Requested'),
        ('APPROVED', 'Approved'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paperwork = models.ForeignKey(PaperWork, on_delete=models.CASCADE, related_name='reviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']

class Version(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paperwork = models.ForeignKey(PaperWork, on_delete=models.CASCADE, related_name='versions')
    version_no = models.PositiveIntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    pdf_path = models.CharField(max_length=255, blank=True, null=True)
    latex_path = models.CharField(max_length=255, blank=True, null=True)
    python_path = models.CharField(max_length=255, blank=True, null=True)
    docx_path = models.CharField(max_length=255, blank=True, null=True)
    ai_percent_self = models.FloatField(default=0.0)
    ai_percent_verified = models.FloatField(default=0.0, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Version'
        verbose_name_plural = 'Versions'
        ordering = ['-version_no']

class Notification(models.Model):
    EVENT_CHOICES = (
        ('WORK_ASSIGNED', 'Work Assigned'),
        ('SUBMITTED', 'Submitted'),
        ('CHANGES_REQUESTED', 'Changes Requested'),
        ('APPROVED', 'Approved'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    paper = models.ForeignKey(PaperWork, on_delete=models.CASCADE, related_name='notifications')
    at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-at']
