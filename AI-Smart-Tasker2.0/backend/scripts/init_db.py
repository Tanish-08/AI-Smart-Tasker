"""Database initialization script."""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hydra import compose, initialize
from backend.app.utils.database import init_database, create_tables, close_database
from backend.app.models import User, Task, Analytics

def main():
    """Initialize the database with tables."""
    print("Initializing database...")

    try:
        # Load configuration
        with initialize(version_base=None, config_path="../config"):
            cfg = compose(config_name="config")

        # Initialize database
        init_database(cfg)
        print("Database connection initialized")

        # Create tables
        create_tables()
        print("Database tables created successfully")

        # Close connections
        close_database()
        print("Database initialization complete!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
