"""
Unit tests for Smart Task Analyzer scoring algorithm.
"""
from django.test import TestCase
from datetime import date, timedelta
from .scoring import TaskScoringEngine


class TaskScoringEngineTests(TestCase):
    """Test suite for TaskScoringEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = TaskScoringEngine(strategy='smart_balance')
        self.today = date.today()
    
    def test_urgency_score_overdue_task(self):
        """Test that overdue tasks receive high urgency scores."""
        overdue_date = self.today - timedelta(days=5)
        score = self.engine.calculate_urgency_score(overdue_date)
        
        # Overdue tasks should score > 10
        self.assertGreater(score, 10.0)
        self.assertLessEqual(score, 15.0)
    
    def test_urgency_score_due_today(self):
        """Test that tasks due today receive maximum urgency."""
        score = self.engine.calculate_urgency_score(self.today)
        self.assertEqual(score, 10.0)
    
    def test_urgency_score_future_task(self):
        """Test that future tasks receive lower urgency scores."""
        future_date = self.today + timedelta(days=30)
        score = self.engine.calculate_urgency_score(future_date)
        
        # Future tasks should have lower urgency
        self.assertLess(score, 7.0)
        self.assertGreaterEqual(score, 1.0)
    
    def test_importance_score_validation(self):
        """Test importance score normalization."""
        # Valid importance values
        self.assertEqual(self.engine.calculate_importance_score(1), 1.0)
        self.assertEqual(self.engine.calculate_importance_score(10), 10.0)
        self.assertEqual(self.engine.calculate_importance_score(5), 5.0)
        
        # Out of range values should be clamped
        self.assertEqual(self.engine.calculate_importance_score(0), 1.0)
        self.assertEqual(self.engine.calculate_importance_score(11), 10.0)
    
    def test_effort_score_quick_wins(self):
        """Test that quick tasks receive higher effort scores."""
        quick_task_score = self.engine.calculate_effort_score(0.5)
        long_task_score = self.engine.calculate_effort_score(10.0)
        
        # Quick tasks should score higher
        self.assertGreater(quick_task_score, long_task_score)
        self.assertEqual(quick_task_score, 10.0)
    
    def test_effort_score_invalid_data(self):
        """Test effort score handles invalid data gracefully."""
        score = self.engine.calculate_effort_score(0)
        self.assertEqual(score, 5.0)  # Default value
        
        score = self.engine.calculate_effort_score(-5)
        self.assertEqual(score, 5.0)  # Default value
    
    def test_dependency_score_blocking_tasks(self):
        """Test that tasks blocking others receive higher dependency scores."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1]},
            {'id': 4, 'dependencies': [1]},
        ]
        
        dep_map = self.engine.build_dependency_map(tasks)
        
        # Task 1 blocks 3 others, should have high score
        score_task_1 = self.engine.calculate_dependency_score(1, tasks, dep_map)
        self.assertGreaterEqual(score_task_1, 8.0)
        
        # Task 4 blocks nothing, should have lower score
        score_task_4 = self.engine.calculate_dependency_score(4, tasks, dep_map)
        self.assertEqual(score_task_4, 3.0)
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        # Create circular dependency: 1 -> 2 -> 3 -> 1
        tasks = [
            {'id': 1, 'dependencies': [3]},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]},
            {'id': 4, 'dependencies': []},
        ]
        
        circular_tasks = self.engine.detect_circular_dependencies(tasks)
        
        # Tasks 1, 2, 3 should be flagged
        self.assertIn(1, circular_tasks)
        self.assertIn(2, circular_tasks)
        self.assertIn(3, circular_tasks)
        self.assertNotIn(4, circular_tasks)
    
    def test_no_circular_dependencies(self):
        """Test that valid dependency chains don't trigger false positives."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]},
        ]
        
        circular_tasks = self.engine.detect_circular_dependencies(tasks)
        self.assertEqual(len(circular_tasks), 0)
    
    def test_analyze_tasks_sorting(self):
        """Test that analyze_tasks correctly sorts by priority."""
        tasks = [
            {
                'id': 1,
                'title': 'Low priority',
                'due_date': self.today + timedelta(days=30),
                'estimated_hours': 10,
                'importance': 2,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'High priority',
                'due_date': self.today + timedelta(days=1),
                'estimated_hours': 2,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Medium priority',
                'due_date': self.today + timedelta(days=7),
                'estimated_hours': 5,
                'importance': 5,
                'dependencies': []
            }
        ]
        
        analyzed = self.engine.analyze_tasks(tasks)
        
        # Should be sorted by priority score (descending)
        self.assertEqual(len(analyzed), 3)
        self.assertGreater(
            analyzed[0]['priority_score'], 
            analyzed[1]['priority_score']
        )
        self.assertGreater(
            analyzed[1]['priority_score'], 
            analyzed[2]['priority_score']
        )
        
        # High priority task should be first
        self.assertEqual(analyzed[0]['id'], 2)
    
    def test_strategy_weights(self):
        """Test that different strategies apply different weights."""
        balanced_engine = TaskScoringEngine(strategy='smart_balance')
        deadline_engine = TaskScoringEngine(strategy='deadline_driven')
        impact_engine = TaskScoringEngine(strategy='high_impact')
        
        # Verify different weight configurations
        self.assertNotEqual(
            balanced_engine.weights['urgency'],
            deadline_engine.weights['urgency']
        )
        self.assertGreater(
            deadline_engine.weights['urgency'],
            balanced_engine.weights['urgency']
        )
        self.assertGreater(
            impact_engine.weights['importance'],
            balanced_engine.weights['importance']
        )
    
    def test_get_top_suggestions(self):
        """Test that get_top_suggestions returns correct number of tasks."""
        tasks = [
            {
                'id': i,
                'title': f'Task {i}',
                'due_date': self.today + timedelta(days=i),
                'estimated_hours': i,
                'importance': 10 - i,
                'dependencies': []
            }
            for i in range(1, 6)
        ]
        
        suggestions = self.engine.get_top_suggestions(tasks, count=3)
        
        # Should return exactly 3 suggestions
        self.assertEqual(len(suggestions), 3)
        
        # Should include rank and recommendation
        for idx, suggestion in enumerate(suggestions, 1):
            self.assertEqual(suggestion['rank'], idx)
            self.assertIn('recommendation', suggestion)
            self.assertIsInstance(suggestion['recommendation'], str)
    
    def test_empty_task_list(self):
        """Test handling of empty task list."""
        result = self.engine.analyze_tasks([])
        self.assertEqual(result, [])
        
        suggestions = self.engine.get_top_suggestions([])
        self.assertEqual(suggestions, [])
    
    def test_score_explanation_generation(self):
        """Test that explanations are generated correctly."""
        task = {
            'id': 1,
            'title': 'Urgent task',
            'due_date': self.today,
            'estimated_hours': 1,
            'importance': 9,
            'dependencies': []
        }
        
        score_breakdown = self.engine.calculate_priority_score(
            task, [task], {}
        )
        
        explanation = self.engine.generate_score_explanation(task, score_breakdown)
        
        # Should contain relevant indicators
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)
        
        # Due today should be mentioned
        self.assertIn('Due TODAY', explanation)
        self.assertIn('High importance', explanation)
    
    def test_build_dependency_map(self):
        """Test dependency map construction."""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1, 2]},
        ]
        
        dep_map = self.engine.build_dependency_map(tasks)
        
        # Task 1 should be blocking 2 tasks
        self.assertEqual(len(dep_map[1]), 2)
        self.assertIn(2, dep_map[1])
        self.assertIn(3, dep_map[1])
        
        # Task 2 should be blocking 1 task
        self.assertEqual(len(dep_map[2]), 1)
        self.assertIn(3, dep_map[2])