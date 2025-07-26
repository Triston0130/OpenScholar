"""Add flashcards column to collection_papers table"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database URL from environment or default
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///openscholar.db')

def add_flashcards_column():
    """Add flashcards JSON column to collection_papers table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pragma_table_info('collection_papers') 
                WHERE name='flashcards'
            """))
            
            if result.scalar() > 0:
                print("Flashcards column already exists")
                return
            
            # Add the flashcards column
            conn.execute(text("""
                ALTER TABLE collection_papers 
                ADD COLUMN flashcards JSON
            """))
            
            conn.commit()
            print("Successfully added flashcards column to collection_papers table")
            
    except SQLAlchemyError as e:
        print(f"Error adding flashcards column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_flashcards_column()