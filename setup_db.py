import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Set up the PostgreSQL database and tables"""
    # Insert mock data into the traffic_detections table
    insert_mock_data()

def insert_mock_data():
    """Insert mock data into the traffic_detections table"""
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    cursor = connection.cursor()
    cursor.execute("""
    cursor.execute("DROP TABLE IF EXISTS traffic_detections;")

    cursor.execute("DROP TABLE IF EXISTS traffic_detections;")

    cursor.execute("DROP TABLE IF EXISTS traffic_detections;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_detections (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_vehicles INT,
            status VARCHAR(50)
        );
    """)

    # Insert mock data
    cursor.execute("""
        INSERT INTO traffic_detections (timestamp, total_vehicles, status, action) VALUES
        (NOW(), 10, 'Normal', 'None'),
        (NOW(), 15, 'Heavy', 'Redirect'),
        (NOW(), 5, 'Light', 'None'),
        (NOW(), 20, 'Normal', 'None'),
        (NOW(), 0, 'No Traffic', 'None');
    """)

    """)
    connection.commit()
    cursor.close()
    connection.close()

    # Database connection parameters
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": os.getenv("DB_PORT", "5432")
    }
    
    print("Connecting with the following parameters:")
    print(f"Host: {db_params['host']}")
    print(f"User: {db_params['user']}")
    print(f"Port: {db_params['port']}")


    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": os.getenv("DB_PORT", "5432")
    }
    
    # Connect to default database to create our database if it doesn't exist
    conn = psycopg2.connect(**db_params, database="postgres")
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    db_name = os.getenv("DB_NAME", "traffic_db")
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating database {db_name}...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database {db_name} created successfully!")
    else:
        print(f"Database {db_name} already exists.")
    
    cursor.close()
    conn.close()
    
    # Connect to our database and create tables
    conn = psycopg2.connect(**db_params, database=db_name)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Read SQL file
    with open('setup_database.sql', 'r') as f:
        sql_script = f.read()
    
    # Execute SQL commands
    print("Setting up tables...")
    cursor.execute(sql_script)
    print("Database setup completed successfully!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup_database()
