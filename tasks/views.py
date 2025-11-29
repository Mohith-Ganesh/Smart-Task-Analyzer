"""
API views for Smart Task Analyzer.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Task
from .serializers import (
    TaskSerializer,
    TaskAnalysisInputSerializer,
    TaskSuggestionInputSerializer,
    TaskAnalysisOutputSerializer,
    TaskSuggestionOutputSerializer
)
from .scoring import TaskScoringEngine
import logging

logger = logging.getLogger(__name__)




@api_view(['GET', 'POST'])
def task_list(request):
    """
    GET /api/tasks/ - List all tasks
    POST /api/tasks/ - Create a new task
    """
    if request.method == 'GET':
        try:
            tasks = Task.objects.all()
            serializer = TaskSerializer(tasks, many=True)
            return Response({
                'status': 'success',
                'count': tasks.count(),
                'tasks': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in task_list GET: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'Failed to retrieve tasks',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = TaskSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid task data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task = serializer.save()
            
            return Response({
                'status': 'success',
                'message': 'Task created successfully',
                'task': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in task_list POST: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'Failed to create task',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def task_detail(request, task_id):
    """
    GET /api/tasks/<id>/ - Get a specific task
    PUT /api/tasks/<id>/ - Update a specific task
    DELETE /api/tasks/<id>/ - Delete a specific task
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'Task with id {task_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response({
            'status': 'success',
            'task': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TaskSerializer(task, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid task data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_task = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Task updated successfully',
            'task': TaskSerializer(updated_task).data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        task.delete()
        return Response({
            'status': 'success',
            'message': f'Task {task_id} deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def bulk_create_tasks(request):
    """
    POST /api/tasks/bulk/ - Create multiple tasks at once
    
    Request Body:
    {
        "tasks": [
            {
                "title": "Task 1",
                "due_date": "2025-11-30",
                "estimated_hours": 3,
                "importance": 8,
                "dependencies": []
            },
            ...
        ]
    }
    """
    try:
        tasks_data = request.data.get('tasks', [])
        
        if not tasks_data:
            return Response({
                'status': 'error',
                'message': 'No tasks provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        created_tasks = []
        errors = []
        
        for idx, task_data in enumerate(tasks_data):
            serializer = TaskSerializer(data=task_data)
            
            if serializer.is_valid():
                task = serializer.save()
                created_tasks.append(TaskSerializer(task).data)
            else:
                errors.append({
                    'index': idx,
                    'data': task_data,
                    'errors': serializer.errors
                })
        
        response_data = {
            'status': 'success' if not errors else 'partial',
            'created_count': len(created_tasks),
            'created_tasks': created_tasks
        }
        
        if errors:
            response_data['failed_count'] = len(errors)
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in bulk_create_tasks: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'Failed to create tasks',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_all_tasks(request):
    """
    DELETE /api/tasks/all/ - Delete all tasks (useful for testing)
    """
    try:
        count = Task.objects.count()
        Task.objects.all().delete()
        
        return Response({
            'status': 'success',
            'message': f'Deleted {count} tasks'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in delete_all_tasks: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'Failed to delete tasks',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def analyze_tasks(request):
    """
    POST /api/tasks/analyze/
    
    Analyze all tasks from database or provided task list.
    Returns them sorted by priority score.
    
    Request Body (Optional):
    {
        "strategy": "smart_balance",  // optional, default: smart_balance
        "use_database": true  // optional, default: true (use database tasks)
    }
    
    OR provide tasks directly:
    {
        "tasks": [...],  // if provided, uses these instead of database
        "strategy": "smart_balance"
    }
    """
    try:
        use_database = request.data.get('use_database', True)
        strategy = request.data.get('strategy', 'smart_balance')
        
        # Check if tasks are provided in request
        if 'tasks' in request.data and request.data['tasks']:
            # Use provided tasks (original behavior)
            input_serializer = TaskAnalysisInputSerializer(data=request.data)
            
            if not input_serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid input data',
                    'errors': input_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = input_serializer.validated_data
            tasks = validated_data['tasks']
            strategy = validated_data.get('strategy', 'smart_balance')
        else:
            # Use database tasks
            db_tasks = Task.objects.all()
            
            if not db_tasks.exists():
                return Response({
                    'status': 'error',
                    'message': 'No tasks found in database. Please create tasks first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Convert database tasks to dict format
            tasks = []
            for task in db_tasks:
                tasks.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': task.due_date,
                    'estimated_hours': task.estimated_hours,
                    'importance': task.importance,
                    'dependencies': task.dependencies
                })
        
        # Initialize scoring engine with strategy
        scoring_engine = TaskScoringEngine(strategy=strategy)
        
        # Analyze tasks
        analyzed_tasks = scoring_engine.analyze_tasks(tasks)
        
        # Serialize output
        output_serializer = TaskAnalysisOutputSerializer(
            analyzed_tasks, 
            many=True
        )
        
        return Response({
            'status': 'success',
            'strategy': strategy,
            'source': 'database' if use_database else 'request',
            'total_tasks': len(analyzed_tasks),
            'tasks': output_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in analyze_tasks: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'An error occurred while analyzing tasks',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def suggest_tasks(request):
    """
    POST /api/tasks/suggest/
    
    Get top N task suggestions from database or provided task list.
    Returns tasks with detailed recommendations.
    
    Request Body (Optional):
    {
        "strategy": "smart_balance",  // optional
        "count": 3,  // optional, default: 3
        "use_database": true  // optional, default: true
    }
    
    OR provide tasks directly:
    {
        "tasks": [...],
        "strategy": "smart_balance",
        "count": 3
    }
    """
    try:
        use_database = request.data.get('use_database', True)
        strategy = request.data.get('strategy', 'smart_balance')
        count = request.data.get('count', 3)
        
        # Check if tasks are provided in request
        if 'tasks' in request.data and request.data['tasks']:
            # Use provided tasks
            input_serializer = TaskSuggestionInputSerializer(data=request.data)
            
            if not input_serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid input data',
                    'errors': input_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = input_serializer.validated_data
            tasks = validated_data['tasks']
            strategy = validated_data.get('strategy', 'smart_balance')
            count = validated_data.get('count', 3)
        else:
            # Use database tasks
            db_tasks = Task.objects.all()
            
            if not db_tasks.exists():
                return Response({
                    'status': 'error',
                    'message': 'No tasks found in database. Please create tasks first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Convert database tasks to dict format
            tasks = []
            for task in db_tasks:
                tasks.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': task.due_date,
                    'estimated_hours': task.estimated_hours,
                    'importance': task.importance,
                    'dependencies': task.dependencies
                })
        
        # Initialize scoring engine with strategy
        scoring_engine = TaskScoringEngine(strategy=strategy)
        
        # Get top suggestions
        suggestions = scoring_engine.get_top_suggestions(tasks, count=count)
        
        # Serialize output
        output_serializer = TaskSuggestionOutputSerializer(
            suggestions, 
            many=True
        )
        
        return Response({
            'status': 'success',
            'strategy': strategy,
            'source': 'database' if use_database else 'request',
            'suggestion_count': len(suggestions),
            'suggestions': output_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in suggest_tasks: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'An error occurred while generating suggestions',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/health/
    
    Simple health check endpoint to verify API is running.
    """
    task_count = Task.objects.count()
    
    return Response({
        'status': 'healthy',
        'message': 'Smart Task Analyzer API is running',
        'database_tasks': task_count,
        'available_endpoints': [
            'GET /api/tasks/ - List all tasks',
            'POST /api/tasks/ - Create a task',
            'GET /api/tasks/<id>/ - Get task details',
            'PUT /api/tasks/<id>/ - Update a task',
            'DELETE /api/tasks/<id>/ - Delete a task',
            'POST /api/tasks/bulk/ - Create multiple tasks',
            'DELETE /api/tasks/all/ - Delete all tasks',
            'POST /api/tasks/analyze/ - Analyze tasks',
            'POST /api/tasks/suggest/ - Get task suggestions',
            'GET /api/health/ - Health check'
        ],
        'available_strategies': [
            'smart_balance',
            'fastest_wins',
            'high_impact',
            'deadline_driven'
        ]
    }, status=status.HTTP_200_OK)