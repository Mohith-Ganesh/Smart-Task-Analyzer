"""
Serializers for Task API endpoints.
"""
from rest_framework import serializers
from .models import Task
from datetime import date


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with validation."""
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'due_date', 'estimated_hours', 
                 'importance', 'dependencies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_importance(self, value):
        """Validate importance is within 1-10 range."""
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                "Importance must be between 1 and 10"
            )
        return value
    
    def validate_estimated_hours(self, value):
        """Validate estimated hours is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Estimated hours must be greater than 0"
            )
        return value
    
    def validate_dependencies(self, value):
        """Validate dependencies is a list of integers."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Dependencies must be a list"
            )
        
        for dep_id in value:
            if not isinstance(dep_id, int):
                raise serializers.ValidationError(
                    "Each dependency must be an integer task ID"
                )
        
        return value


class TaskAnalysisInputSerializer(serializers.Serializer):
    """Serializer for task analysis input."""
    
    tasks = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        help_text="List of tasks to analyze"
    )
    
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        default='smart_balance',
        required=False,
        help_text="Scoring strategy to use"
    )
    
    def validate_tasks(self, value):
        """Validate each task has required fields."""
        required_fields = ['title', 'due_date', 'estimated_hours', 'importance']
        
        for idx, task in enumerate(value):
            # Check required fields
            for field in required_fields:
                if field not in task:
                    raise serializers.ValidationError(
                        f"Task at index {idx} missing required field: {field}"
                    )
            
            # Validate field types and values
            try:
                # Convert due_date string to date object
                if isinstance(task['due_date'], str):
                    task['due_date'] = date.fromisoformat(task['due_date'])
                
                # Validate importance range
                importance = int(task['importance'])
                if importance < 1 or importance > 10:
                    raise serializers.ValidationError(
                        f"Task at index {idx}: importance must be 1-10"
                    )
                task['importance'] = importance
                
                # Validate estimated hours
                hours = float(task['estimated_hours'])
                if hours <= 0:
                    raise serializers.ValidationError(
                        f"Task at index {idx}: estimated_hours must be positive"
                    )
                task['estimated_hours'] = hours
                
                # Ensure dependencies is a list
                if 'dependencies' not in task:
                    task['dependencies'] = []
                elif not isinstance(task['dependencies'], list):
                    raise serializers.ValidationError(
                        f"Task at index {idx}: dependencies must be a list"
                    )
                
                # Add ID if not present (for analysis purposes)
                if 'id' not in task:
                    task['id'] = idx + 1
                
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError(
                    f"Task at index {idx}: invalid data type - {str(e)}"
                )
        
        return value


class TaskSuggestionInputSerializer(serializers.Serializer):
    """Serializer for task suggestion input."""
    
    tasks = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        help_text="List of tasks to get suggestions from"
    )
    
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        default='smart_balance',
        required=False,
        help_text="Scoring strategy to use"
    )
    
    count = serializers.IntegerField(
        default=3,
        min_value=1,
        max_value=10,
        required=False,
        help_text="Number of suggestions to return"
    )
    
    def validate_tasks(self, value):
        """Reuse validation from TaskAnalysisInputSerializer."""
        serializer = TaskAnalysisInputSerializer(data={'tasks': value})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data['tasks']


class TaskAnalysisOutputSerializer(serializers.Serializer):
    """Serializer for task analysis output."""
    
    id = serializers.IntegerField()
    title = serializers.CharField()
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    priority_score = serializers.FloatField()
    explanation = serializers.CharField()
    has_circular_dependency = serializers.BooleanField()
    score_breakdown = serializers.DictField()


class TaskSuggestionOutputSerializer(TaskAnalysisOutputSerializer):
    """Serializer for task suggestion output with additional fields."""
    
    rank = serializers.IntegerField()
    recommendation = serializers.CharField()