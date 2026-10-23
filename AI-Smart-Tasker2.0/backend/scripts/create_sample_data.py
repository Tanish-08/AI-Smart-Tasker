"""Create sample data for testing."""
import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hydra import compose, initialize
from backend.app.utils.database import init_database, get_db, close_database
from backend.app.models.user import User
from backend.app.models.task import Task


def create_sample_user(db):
    """Create a sample user."""
    user = User(
        username="demo_user",
        email="demo@example.com",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user: {user.username} (ID: {user.id})")
    return user


def create_sample_tasks(db, user_id):
    """Create sample tasks for testing."""
    tasks = [
        {
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication to the API",
            "deadline": datetime.utcnow() + timedelta(days=2),
            "completed": False
        },
        {
            "title": "Write API documentation",
            "description": "Complete OpenAPI documentation for all endpoints",
            "deadline": datetime.utcnow() + timedelta(days=5),
            "completed": False
        },
        {
            "title": "Fix database connection pool",
            "description": "Investigate and fix connection pool exhaustion issue",
            "deadline": datetime.utcnow() - timedelta(days=1),  # Overdue
            "completed": False
        },
        {
            "title": "Update dependencies",
            "description": "Update all Python packages to latest versions",
            "deadline": datetime.utcnow() + timedelta(hours=12),
            "completed": False
        },
        {
            "title": "Setup CI/CD pipeline",
            "description": "Configure GitHub Actions for automated testing",
            "deadline": datetime.utcnow() - timedelta(days=3),  # Overdue
            "completed": False
        }
    ]

    created_tasks = []
    for task_data in tasks:
        task = Task(
            user_id=user_id,
            **task_data
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    print(f"Created {len(created_tasks)} sample tasks")

    for task in created_tasks:
        db.refresh(task)
        status = "OVERDUE" if task.is_overdue else "PENDING"
        print(f"  - [{status}] {task.title}")

    return created_tasks


def main():
    """Create sample data."""
    print("Creating sample data...")

    try:
        # Load configuration
        with initialize(version_base=None, config_path="../config"):
            cfg = compose(config_name="config")

        # Initialize database
        init_database(cfg)
        print("Database connection initialized")

        # Get database session
        db = next(get_db())

        # Check if demo user already exists
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if existing_user:
            print(f"Demo user already exists (ID: {existing_user.id})")
            user = existing_user
        else:
            # Create sample user
            user = create_sample_user(db)

        # Create sample tasks
        create_sample_tasks(db, user.id)

        # Close database
        db.close()
        close_database()

        print("\nSample data created successfully!")
        print(f"\nYou can now test the API with user_id={user.id}")
        print("Try these endpoints:")
        print(f"  GET /api/tasks?user_id={user.id}")
        print(f"  GET /api/deadlines/check?user_id={user.id}")
        print(f"  GET /api/analytics?user_id={user.id}")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
