"""
Task model definition for the Smart Task Analyzer.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Task(models.Model):
    """
    Task model representing a user task with priority scoring capabilities.
    """
    title = models.CharField(max_length=255, help_text="Task title/description")
    
    due_date = models.DateField(
        help_text="Task deadline"
    )
    
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Estimated effort in hours"
    )
    
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="User-defined importance rating (1-10)"
    )
    
    # Store dependencies as JSON array of task IDs
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of task IDs that this task depends on"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} (Due: {self.due_date})"
    
    def is_overdue(self):
        """Check if task is past its due date."""
        return self.due_date < timezone.now().date()
    
    def days_until_due(self):
        """Calculate days remaining until due date (negative if overdue)."""
        delta = self.due_date - timezone.now().date()
        return delta.days