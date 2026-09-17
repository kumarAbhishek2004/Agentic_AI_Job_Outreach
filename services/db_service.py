import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'outreach.db')

def init_db():
    """Initializes the SQLite database with the necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Contacts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sno TEXT,
            name TEXT,
            email TEXT UNIQUE,
            title TEXT,
            company TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Create Campaigns (Emails) Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            status TEXT DEFAULT 'drafted',
            subject TEXT,
            body_draft TEXT,
            resume_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            message_id TEXT,
            error_log TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    ''')

    # Create Company Cache Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_cache (
            company TEXT PRIMARY KEY,
            industry TEXT,
            summary TEXT,
            skills_required TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def import_contacts_from_excel(file_path):
    """Reads the HR contacts from Excel and inserts them into the DB."""
    try:
        # Based on the file structure, the actual headers are on row 1 (index 1)
        # Columns are SNo, Name, Email, Title, Company
        df = pd.read_excel(file_path, header=1)
        
        # Clean up column names by stripping whitespace
        df.columns = df.columns.str.strip()
        
        # Ensure required columns exist
        required_cols = ['SNo', 'Name', 'Email', 'Title', 'Company']
        for col in required_cols:
            if col not in df.columns:
                print(f"Warning: Expected column '{col}' not found. Available columns: {list(df.columns)}")
                return 0

        # Drop rows where Email is empty
        df = df.dropna(subset=['Email'])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted_count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO contacts (sno, name, email, title, company, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                ''', (str(row['SNo']), str(row['Name']), str(row['Email']), str(row['Title']), str(row['Company'])))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Email already exists, skip
                continue
                
        conn.commit()
        conn.close()
        
        print(f"Successfully imported {inserted_count} new contacts.")
        return inserted_count
        
    except Exception as e:
        print(f"Error importing Excel: {e}")
        return 0

def get_pending_contacts(limit=40):
    """Fetches a batch of pending contacts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM contacts 
        WHERE status = 'pending' 
        LIMIT ?
    ''')
    
    contacts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return contacts

if __name__ == "__main__":
    init_db()
    # Test import (assuming running from services directory)
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contacts', 'hr.xlsx')
    if os.path.exists(excel_path):
        print(f"Found Excel file at {excel_path}, importing...")
        import_contacts_from_excel(excel_path)
    else:
        print(f"Excel file not found at {excel_path}")
