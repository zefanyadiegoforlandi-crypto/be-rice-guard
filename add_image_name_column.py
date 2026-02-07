"""Add image_name column to detections table"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.models.database_init import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'detections' AND COLUMN_NAME = 'image_name'"
        ))
        exists = result.scalar()

        if exists:
            print("Column 'image_name' already exists. Skipping.")
        else:
            conn.execute(text(
                "ALTER TABLE detections ADD COLUMN image_name VARCHAR(255) NULL AFTER user_id"
            ))
            conn.commit()
            print("Column 'image_name' added to 'detections' table successfully!")

if __name__ == "__main__":
    migrate()
