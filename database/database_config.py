"""
Database Configuration for Population Density Analyzer
Update the DATABASE_URL below with your PostgreSQL credentials.
"""

# PostgreSQL Database Configuration
# Format: postgresql://username:password@host:port/database
DATABASE_URL = "postgresql://population_user:population123@localhost:5432/population_db"

# Alternative configurations (uncomment to use):
# DATABASE_URL = "postgresql://postgres:your_postgres_password@localhost:5432/population_db"

# Instructions:
# 1. Update the DATABASE_URL above with your actual PostgreSQL credentials
# 2. Make sure PostgreSQL is running
# 3. Run: python setup_postgres.py
# 4. Start the app: streamlit run "population_density.py"
