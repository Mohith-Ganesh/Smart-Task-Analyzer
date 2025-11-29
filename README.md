# Smart Task Analyzer

A Django-based intelligent task management system that scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone or extract the repository**
```bash
cd task-analyzer
```

2. **Create and activate virtual environment**
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser (optional, for admin access)**
```bash
python manage.py createsuperuser
```

6. **Run the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### Running Tests
```bash
python manage.py test tasks
```

## 📋 API Endpoints

### 1. Health Check
**GET** `/api/health/`

Verify the API is running and see available endpoints.

**Response:**
```json
{
  "status": "healthy",
  "message": "Smart Task Analyzer API is running",
  "database_tasks": 5,
  "available_endpoints": [...],
  "available_strategies": [...]
}
```

### 2. Task Management (CRUD)

#### List All Tasks
**GET** `/api/tasks/`

Get all tasks from the database.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "tasks": [
    {
      "id": 1,
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": [],
      "created_at": "2025-11-29T10:00:00Z",
      "updated_at": "2025-11-29T10:00:00Z"
    }
  ]
}
```

#### Create a Task
**POST** `/api/tasks/`

Create a single task in the database.

**Request Body:**
```json
{
  "title": "Fix login bug",
  "due_date": "2025-11-30",
  "estimated_hours": 3,
  "importance": 8,
  "dependencies": []
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task created successfully",
  "task": {
    "id": 1,
    "title": "Fix login bug",
    ...
  }
}
```

#### Get Task Details
**GET** `/api/tasks/<id>/`

Get details of a specific task.

#### Update a Task
**PUT** `/api/tasks/<id>/`

Update a specific task (partial updates supported).

**Request Body:**
```json
{
  "importance": 9,
  "estimated_hours": 2
}
```

#### Delete a Task
**DELETE** `/api/tasks/<id>/`

Delete a specific task.

#### Bulk Create Tasks
**POST** `/api/tasks/bulk/`

Create multiple tasks at once.

**Request Body:**
```json
{
  "tasks": [
    {
      "title": "Task 1",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    },
    {
      "title": "Task 2",
      "due_date": "2025-12-01",
      "estimated_hours": 5,
      "importance": 7,
      "dependencies": [1]
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "created_count": 2,
  "created_tasks": [...],
  "failed_count": 0,
  "errors": []
}
```

#### Delete All Tasks
**DELETE** `/api/tasks/all/`

Delete all tasks from the database (useful for testing).

### 3. Analyze Tasks
**POST** `/api/tasks/analyze/`

Analyze tasks and return them sorted by priority score.

**By default, analyzes tasks from the database:**
```json
{
  "strategy": "smart_balance"
}
```

**Or provide tasks directly:**
```json
{
  "tasks": [
    {
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ],
  "strategy": "smart_balance"
}
```

**Response:**
```json
{
  "status": "success",
  "strategy": "smart_balance",
  "source": "database",
  "total_tasks": 5,
  "tasks": [
    {
      "id": 1,
      "title": "Fix login bug",
      "priority_score": 8.75,
      "explanation": "Due in 1 days | High importance (8/10)",
      "has_circular_dependency": false,
      "score_breakdown": {...}
    }
  ]
}
```

### 4. Get Task Suggestions
**POST** `/api/tasks/suggest/`

Get top N task recommendations with detailed explanations.

**By default, uses tasks from the database:**
```json
{
  "strategy": "smart_balance",
  "count": 3
}
```

**Or provide tasks directly:**
```json
{
  "tasks": [...],
  "strategy": "smart_balance",
  "count": 3
}
```

**Response:**
```json
{
  "status": "success",
  "strategy": "smart_balance",
  "source": "database",
  "suggestion_count": 3,
  "suggestions": [
    {
      "rank": 1,
      "id": 1,
      "title": "Fix login bug",
      "priority_score": 8.75,
      "recommendation": "Recommended #1 due to: urgent deadline, high impact",
      ...
    }
  ]
}
```

### Priority Scoring System

The Smart Task Analyzer uses a sophisticated multi-factor scoring algorithm that evaluates tasks across four key dimensions:

#### 1. **Urgency Score** (Weight: 35%)
Calculates time sensitivity based on due date:
- **Overdue tasks**: Exponentially increasing score (10.0 - 15.0) based on days overdue
- **Due today**: Maximum urgency (10.0)
- **Due within 3 days**: Very high urgency (9.0)
- **Due within 1 week**: High urgency (7.0 - 8.75)
- **Due within 2 weeks**: Medium urgency (5.1 - 6.5)
- **Due within 30 days**: Lower urgency (3.6 - 4.5)
- **Due later**: Asymptotic decay using logarithmic function

This approach ensures overdue tasks receive immediate attention while properly prioritizing upcoming deadlines.

#### 2. **Importance Score** (Weight: 30%)
Direct user-provided rating on a 1-10 scale:
- Reflects the strategic value or business impact of the task
- Allows users to express subjective priority judgments
- Normalized and validated to ensure consistency

#### 3. **Effort Score** (Weight: 15%)
Inverse relationship where lower effort = higher score:
- **< 1 hour**: 10.0 (quick wins)
- **1-2 hours**: 9.0
- **2-4 hours**: 6.5 - 8.0
- **4-8 hours**: 5.0 - 6.0
- **8+ hours**: 1.0 - 5.0 (logarithmic decay)

This encourages completing "quick wins" that provide momentum and psychological benefits.

#### 4. **Dependency Score** (Weight: 20%)
Evaluates how many other tasks depend on this task:
- **Blocks 3+ tasks**: 10.0 (critical path)
- **Blocks 2 tasks**: 8.0
- **Blocks 1 task**: 6.0
- **Blocks 0 tasks**: 3.0 (baseline)

Uses reverse dependency mapping to identify blocking tasks that should be prioritized to unblock workflows.

### Scoring Strategies

The algorithm supports four configurable strategies with different weight distributions:

1. **Smart Balance** (Default)
   - Urgency: 35%, Importance: 30%, Effort: 15%, Dependencies: 20%
   - Well-rounded approach for general use

2. **Fastest Wins**
   - Urgency: 20%, Importance: 20%, Effort: 50%, Dependencies: 10%
   - Prioritizes quick, achievable tasks

3. **High Impact**
   - Urgency: 15%, Importance: 60%, Effort: 10%, Dependencies: 15%
   - Focuses on strategic importance

4. **Deadline Driven**
   - Urgency: 60%, Importance: 20%, Effort: 5%, Dependencies: 15%
   - Prioritizes time-sensitive tasks

## API Usage Examples

### Workflow: Create Tasks → Analyze → Get Suggestions

### Step 1: Create Tasks in Database

#### Using cURL

```bash
# Create a single task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix critical bug",
    "due_date": "2025-11-29",
    "estimated_hours": 2,
    "importance": 10,
    "dependencies": []
  }'

# Create multiple tasks at once
curl -X POST http://localhost:8000/api/tasks/bulk/ \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "Fix login bug",
        "due_date": "2025-11-30",
        "estimated_hours": 3,
        "importance": 8,
        "dependencies": []
      },
      {
        "title": "Write documentation",
        "due_date": "2025-12-05",
        "estimated_hours": 5,
        "importance": 6,
        "dependencies": [1]
      },
      {
        "title": "Deploy to production",
        "due_date": "2025-12-01",
        "estimated_hours": 1,
        "importance": 9,
        "dependencies": [1]
      }
    ]
  }'
```

### Step 2: List All Tasks

```bash
# Get all tasks from database
curl http://localhost:8000/api/tasks/
```

### Step 3: Analyze Tasks

```bash
# Analyze all tasks in database
curl -X POST http://localhost:8000/api/tasks/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "smart_balance"
  }'

# Or analyze with different strategy
curl -X POST http://localhost:8000/api/tasks/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "deadline_driven"
  }'
```

### Step 4: Get Task Suggestions

```bash
# Get top 3 suggestions from database
curl -X POST http://localhost:8000/api/tasks/suggest/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "smart_balance",
    "count": 3
  }'
```

### Update and Delete Tasks

```bash
# Update a task
curl -X PUT http://localhost:8000/api/tasks/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "importance": 10,
    "estimated_hours": 1
  }'

# Get specific task
curl http://localhost:8000/api/tasks/1/

# Delete specific task
curl -X DELETE http://localhost:8000/api/tasks/1/

# Delete all tasks
curl -X DELETE http://localhost:8000/api/tasks/all/
```

### Using Python

```python
import requests

base_url = "http://localhost:8000/api"

# Step 1: Create tasks
tasks_data = {
    "tasks": [
        {
            "title": "Implement feature X",
            "due_date": "2025-12-01",
            "estimated_hours": 5,
            "importance": 7,
            "dependencies": []
        },
        {
            "title": "Fix bug Y",
            "due_date": "2025-11-30",
            "estimated_hours": 2,
            "importance": 9,
            "dependencies": []
        }
    ]
}

response = requests.post(f"{base_url}/tasks/bulk/", json=tasks_data)
print("Created tasks:", response.json())

# Step 2: List all tasks
response = requests.get(f"{base_url}/tasks/")
print("All tasks:", response.json())

# Step 3: Analyze tasks (uses database by default)
response = requests.post(f"{base_url}/tasks/analyze/", json={
    "strategy": "smart_balance"
})
print("Analysis:", response.json())

# Step 4: Get suggestions
response = requests.post(f"{base_url}/tasks/suggest/", json={
    "strategy": "high_impact",
    "count": 3
})
print("Suggestions:", response.json())

# Update a task
response = requests.put(f"{base_url}/tasks/1/", json={
    "importance": 10
})
print("Updated task:", response.json())
```

### Using JavaScript (Fetch API)

```javascript
const baseUrl = "http://localhost:8000/api";

// Create tasks
async function createTasks() {
  const response = await fetch(`${baseUrl}/tasks/bulk/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tasks: [
        {
          title: "Complete project",
          due_date: "2025-12-01",
          estimated_hours: 8,
          importance: 9,
          dependencies: []
        }
      ]
    })
  });
  return await response.json();
}

// Analyze tasks
async function analyzeTasks() {
  const response = await fetch(`${baseUrl}/tasks/analyze/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      strategy: "smart_balance"
    })
  });
  return await response.json();
}

// Get suggestions
async function getSuggestions() {
  const response = await fetch(`${baseUrl}/tasks/suggest/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      strategy: "deadline_driven",
      count: 5
    })
  });
  return await response.json();
}

// Usage
createTasks()
  .then(data => console.log("Created:", data))
  .then(() => analyzeTasks())
  .then(data => console.log("Analysis:", data))
  .then(() => getSuggestions())
  .then(data => console.log("Suggestions:", data));
```
