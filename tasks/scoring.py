"""
Smart Task Analyzer - Priority Scoring Algorithm

This module implements the core priority scoring logic that evaluates tasks
based on multiple factors: urgency, importance, effort, and dependencies.
"""

from datetime import date
from typing import List, Dict, Set, Optional
import math


class TaskScoringEngine:
    """
    Advanced task priority scoring engine with configurable weighting strategies.
    """
    
    # Default weight configuration for balanced scoring
    DEFAULT_WEIGHTS = {
        'urgency': 0.35,
        'importance': 0.30,
        'effort': 0.15,
        'dependencies': 0.20
    }
    
    STRATEGY_WEIGHTS = {
        'fastest_wins': {
            'urgency': 0.20,
            'importance': 0.20,
            'effort': 0.50,
            'dependencies': 0.10
        },
        'high_impact': {
            'urgency': 0.15,
            'importance': 0.60,
            'effort': 0.10,
            'dependencies': 0.15
        },
        'deadline_driven': {
            'urgency': 0.60,
            'importance': 0.20,
            'effort': 0.05,
            'dependencies': 0.15
        },
        'smart_balance': DEFAULT_WEIGHTS
    }
    
    def __init__(self, strategy: str = 'smart_balance'):
        """
        Initialize scoring engine with a specific strategy.
        
        Args:
            strategy: One of 'smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'
        """
        self.weights = self.STRATEGY_WEIGHTS.get(strategy, self.DEFAULT_WEIGHTS)
        self.strategy = strategy
    
    def calculate_urgency_score(self, due_date: date) -> float:
        """
        Calculate urgency score based on time until due date.
        
        Algorithm:
        - Overdue tasks: Exponentially increasing score based on days overdue
        - Due today: Maximum urgency (10.0)
        - Due within 7 days: High urgency (7-10)
        - Due within 30 days: Medium urgency (4-7)
        - Due later: Low urgency (1-4)
        
        Returns:
            Float score between 0 and 10
        """
        today = date.today()
        days_diff = (due_date - today).days
        
        if days_diff < 0:  # Overdue
            # Exponential increase for overdue tasks
            overdue_days = abs(days_diff)
            score = 10.0 + min(overdue_days * 0.5, 5.0)  # Cap at 15.0
            return min(score, 15.0)
        elif days_diff == 0:  # Due today
            return 10.0
        elif days_diff <= 3:
            return 9.0
        elif days_diff <= 7:
            return 8.0 - (days_diff - 3) * 0.25
        elif days_diff <= 14:
            return 6.5 - (days_diff - 7) * 0.2
        elif days_diff <= 30:
            return 4.5 - (days_diff - 14) * 0.1
        else:
            # Asymptotic decay for distant tasks
            return max(1.0, 3.0 - math.log10(days_diff - 29))
    
    def calculate_importance_score(self, importance: int) -> float:
        """
        Normalize importance rating to 0-10 scale.
        
        Args:
            importance: User-provided rating (1-10)
            
        Returns:
            Normalized score
        """
        # Direct mapping, already on correct scale
        return float(max(1, min(10, importance)))
    
    def calculate_effort_score(self, estimated_hours: float) -> float:
        """
        Calculate effort score where lower effort = higher score (quick wins).
        
        Algorithm:
        - Tasks under 1 hour: 10.0 (quick wins)
        - Tasks 1-3 hours: 8-9
        - Tasks 3-8 hours: 5-8
        - Tasks 8+ hours: 2-5
        
        Returns:
            Score between 1 and 10
        """
        if estimated_hours <= 0:
            return 5.0  # Default for invalid data
        
        if estimated_hours < 1:
            return 10.0
        elif estimated_hours <= 2:
            return 9.0
        elif estimated_hours <= 4:
            return 8.0 - (estimated_hours - 2) * 0.5
        elif estimated_hours <= 8:
            return 6.0 - (estimated_hours - 4) * 0.25
        else:
            # Logarithmic decay for very long tasks
            return max(1.0, 5.0 - math.log10(estimated_hours - 7))
    
    def calculate_dependency_score(self, task_id: int, all_tasks: List[Dict], 
                                   dependency_map: Dict[int, List[int]]) -> float:
        """
        Calculate dependency score based on how many tasks depend on this one.
        
        Tasks that block other tasks should have higher priority.
        
        Args:
            task_id: Current task ID
            all_tasks: List of all task dictionaries
            dependency_map: Map of task_id -> list of dependent task IDs
            
        Returns:
            Score between 0 and 10
        """
        # Count how many tasks are blocked by this task
        blocked_count = len(dependency_map.get(task_id, []))
        
        if blocked_count == 0:
            return 3.0  # Base score for tasks with no dependents
        elif blocked_count == 1:
            return 6.0
        elif blocked_count == 2:
            return 8.0
        elif blocked_count >= 3:
            return 10.0
        
        return 5.0
    
    def detect_circular_dependencies(self, tasks: List[Dict]) -> Set[int]:
        """
        Detect circular dependencies using depth-first search.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Set of task IDs involved in circular dependencies
        """
        task_map = {task['id']: task for task in tasks}
        visited = set()
        rec_stack = set()
        circular_tasks = set()
        
        def has_cycle(task_id: int) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = task_map.get(task_id)
            if task and 'dependencies' in task:
                for dep_id in task['dependencies']:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            circular_tasks.add(task_id)
                            return True
                    elif dep_id in rec_stack:
                        circular_tasks.add(task_id)
                        circular_tasks.add(dep_id)
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            task_id = task['id']
            if task_id not in visited:
                has_cycle(task_id)
        
        return circular_tasks
    
    def build_dependency_map(self, tasks: List[Dict]) -> Dict[int, List[int]]:
        """
        Build a reverse dependency map (task -> tasks that depend on it).
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Dictionary mapping task_id to list of dependent task IDs
        """
        dep_map = {}
        
        for task in tasks:
            task_id = task.get('id')
            dependencies = task.get('dependencies', [])
            
            for dep_id in dependencies:
                if dep_id not in dep_map:
                    dep_map[dep_id] = []
                dep_map[dep_id].append(task_id)
        
        return dep_map
    
    def calculate_priority_score(self, task: Dict, all_tasks: List[Dict], 
                                dependency_map: Dict[int, List[int]]) -> Dict:
        """
        Calculate comprehensive priority score for a task.
        
        Args:
            task: Task dictionary with all required fields
            all_tasks: List of all tasks for dependency analysis
            dependency_map: Reverse dependency mapping
            
        Returns:
            Dictionary with score and component breakdown
        """
        # Extract task data with validation
        due_date = task.get('due_date')
        importance = task.get('importance', 5)
        estimated_hours = task.get('estimated_hours', 1)
        task_id = task.get('id')
        
        # Calculate individual component scores
        urgency_score = self.calculate_urgency_score(due_date)
        importance_score = self.calculate_importance_score(importance)
        effort_score = self.calculate_effort_score(estimated_hours)
        dependency_score = self.calculate_dependency_score(
            task_id, all_tasks, dependency_map
        )
        
        # Calculate weighted total score
        total_score = (
            urgency_score * self.weights['urgency'] +
            importance_score * self.weights['importance'] +
            effort_score * self.weights['effort'] +
            dependency_score * self.weights['dependencies']
        )
        
        return {
            'total_score': round(total_score, 2),
            'urgency_score': round(urgency_score, 2),
            'importance_score': round(importance_score, 2),
            'effort_score': round(effort_score, 2),
            'dependency_score': round(dependency_score, 2),
            'weights_used': self.weights.copy()
        }
    
    def generate_score_explanation(self, task: Dict, score_breakdown: Dict) -> str:
        """
        Generate human-readable explanation for why task received its score.
        
        Args:
            task: Task dictionary
            score_breakdown: Score components from calculate_priority_score
            
        Returns:
            Explanation string
        """
        explanations = []
        
        # Urgency explanation
        days_diff = (task['due_date'] - date.today()).days
        if days_diff < 0:
            explanations.append(f"OVERDUE by {abs(days_diff)} days")
        elif days_diff == 0:
            explanations.append("Due TODAY")
        elif days_diff <= 3:
            explanations.append(f"Due in {days_diff} days")
        elif days_diff <= 7:
            explanations.append(f"Due this week ({days_diff} days)")
        
        # Importance explanation
        if task['importance'] >= 8:
            explanations.append(f"High importance ({task['importance']}/10)")
        elif task['importance'] >= 6:
            explanations.append(f"📌 Medium importance ({task['importance']}/10)")
        
        # Effort explanation
        if task['estimated_hours'] <= 2:
            explanations.append(f"Quick task ({task['estimated_hours']}h)")
        elif task['estimated_hours'] >= 8:
            explanations.append(f"Large task ({task['estimated_hours']}h)")
        
        # Dependency explanation
        dep_score = score_breakdown['dependency_score']
        if dep_score >= 8:
            explanations.append("Blocks multiple tasks")
        elif dep_score >= 6:
            explanations.append("Blocks other tasks")
        
        return " | ".join(explanations) if explanations else "Standard priority task"
    
    def analyze_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Analyze and score all tasks, returning them sorted by priority.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Sorted list of tasks with scores and explanations
        """
        if not tasks:
            return []
        
        # Build dependency map
        dependency_map = self.build_dependency_map(tasks)
        
        # Detect circular dependencies
        circular_deps = self.detect_circular_dependencies(tasks)
        
        # Score each task
        scored_tasks = []
        for task in tasks:
            score_breakdown = self.calculate_priority_score(
                task, tasks, dependency_map
            )
            
            explanation = self.generate_score_explanation(task, score_breakdown)
            
            task_result = {
                **task,
                'priority_score': score_breakdown['total_score'],
                'score_breakdown': score_breakdown,
                'explanation': explanation,
                'has_circular_dependency': task['id'] in circular_deps
            }
            
            scored_tasks.append(task_result)
        
        # Sort by priority score (descending)
        scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return scored_tasks
    
    def get_top_suggestions(self, tasks: List[Dict], count: int = 3) -> List[Dict]:
        """
        Get top N task suggestions with detailed reasoning.
        
        Args:
            tasks: List of task dictionaries
            count: Number of suggestions to return
            
        Returns:
            List of top priority tasks with extended explanations
        """
        scored_tasks = self.analyze_tasks(tasks)
        top_tasks = scored_tasks[:count]
        
        # Add ranking and enhanced explanations
        for idx, task in enumerate(top_tasks, 1):
            task['rank'] = idx
            task['recommendation'] = self._generate_recommendation(task, idx)
        
        return top_tasks
    
    def _generate_recommendation(self, task: Dict, rank: int) -> str:
        """Generate detailed recommendation for a task."""
        reasons = []
        
        breakdown = task['score_breakdown']
        
        if breakdown['urgency_score'] >= 9:
            reasons.append("urgent deadline")
        if breakdown['importance_score'] >= 8:
            reasons.append("high impact")
        if breakdown['effort_score'] >= 8:
            reasons.append("quick completion")
        if breakdown['dependency_score'] >= 7:
            reasons.append("unblocks other work")
        
        if reasons:
            return f"Recommended #{rank} due to: {', '.join(reasons)}"
        else:
            return f"Recommended #{rank} based on balanced priority factors"