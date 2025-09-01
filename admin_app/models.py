from django.db import models
import uuid
from auth_app.models import User

class PaperWork(models.Model):
    STATUS_CHOICES = (
        ('ASSIGNED', 'Assigned'),
        ('SUBMITTED', 'Submitted'),
        ('CHANGES_REQUESTED', 'Changes Requested'),
        ('APPROVED', 'Approved'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    researcher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paperworks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    assigned_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Paper Work'
        verbose_name_plural = 'Paper Works'
