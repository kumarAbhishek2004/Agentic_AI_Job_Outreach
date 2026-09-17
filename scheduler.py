import time
import random
import sqlite3
import datetime
import sys
import os

from services.db_service import DB_PATH
from services.gmail_service import send_email

def get_approved_campaign():
    """Fetches the next approved campaign to send."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id as cid, c.email, camp.id as camp_id, camp.subject, camp.body_draft, camp.resume_used
        FROM contacts c
        JOIN campaigns camp ON c.id = camp.contact_id
        WHERE c.status = 'approved'
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def mark_as_sent(contact_id, camp_id, message_id):
    """Updates the database status to sent."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE campaigns SET status='sent', sent_at=CURRENT_TIMESTAMP, message_id=? WHERE id=?", (message_id, camp_id))
    cursor.execute("UPDATE contacts SET status='sent' WHERE id=?", (contact_id,))
    conn.commit()
    conn.close()

def mark_as_failed(contact_id, camp_id, error_msg):
    """Updates the database status to failed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE campaigns SET status='failed', error_log=? WHERE id=?", (error_msg, camp_id))
    cursor.execute("UPDATE contacts SET status='failed' WHERE id=?", (contact_id,))
    conn.commit()
    conn.close()

def is_working_hours():
    """Checks if the current time is between 9 AM and 7 PM local time."""
    now = datetime.datetime.now()
    return 9 <= now.hour < 19

from config import DAILY_EMAIL_LIMIT
from services.gmail_service import authenticate_gmail, send_email

def get_emails_sent_today():
    """Counts how many emails have been sent today."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM campaigns 
        WHERE status = 'sent' AND date(sent_at) = date('now', 'localtime')
    ''')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def run_scheduler():
    print("🚀 AI Outreach Scheduler Started!")
    print("Verifying Gmail Authentication...")
    
    # Authenticate immediately on startup so the user can grant permission now
    # rather than the script hanging at 9 AM tomorrow waiting for a click.
    auth_service = authenticate_gmail()
    if not auth_service:
        print("❌ Fatal Error: Could not authenticate with Gmail. Stopping.")
        return
        
    print("✅ Gmail Authentication Successful!")
    print(f"Daily Target Limit: {DAILY_EMAIL_LIMIT} emails.")
    print("Monitoring database for 'approved' emails...")
    
    emails_in_current_batch = 0
    # Randomize the batch limit so it doesn't stop at exactly 10 every time
    current_batch_limit = random.randint(8, 15) 
    
    while True:
        # 1. Check Daily Limit (Controlled by config.py)
        sent_today = get_emails_sent_today()
        if sent_today >= DAILY_EMAIL_LIMIT:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] Daily limit of {DAILY_EMAIL_LIMIT} reached. Sleeping for 1 hour...")
            time.sleep(3600)
            continue

        # 2. Check Working Hours (9 AM - 5 PM)
        if not is_working_hours():
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[{now_str}] Outside working hours (9 AM - 5 PM). Sleeping for 30 minutes...")
            time.sleep(1800)
            continue
            
        # 3. Check Batch Limit (Random rest between 25-50 mins)
        if emails_in_current_batch >= current_batch_limit:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            rest_seconds = random.randint(1500, 3000) # 25 to 50 minutes
            print(f"[{now_str}] Sent {emails_in_current_batch} emails. Resting for {rest_seconds // 60} minutes and {rest_seconds % 60} seconds...")
            time.sleep(rest_seconds)
            
            # Reset counters for the next batch
            emails_in_current_batch = 0  
            current_batch_limit = random.randint(8, 15)
            continue
            
        campaign = get_approved_campaign()
        
        if campaign:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"\n[{now_str}] Found approved email for {campaign['email']}")
            print("Authenticating with Gmail and sending...")
            
            success, result = send_email(
                to_address=campaign['email'],
                subject=campaign['subject'],
                body=campaign['body_draft'],
                resume_filename=campaign['resume_used']
            )
            
            if success:
                print(f"✅ Successfully sent! Message ID: {result}")
                mark_as_sent(campaign['cid'], campaign['camp_id'], result)
                emails_in_current_batch += 1
            else:
                print(f"❌ Failed to send: {result}")
                mark_as_failed(campaign['cid'], campaign['camp_id'], result)
                
            # Sleep for a random interval between 3 and 10 minutes (180 - 600 seconds)
            delay = random.randint(180, 600)
            print(f"Sleeping for {delay // 60} minutes and {delay % 60} seconds...")
            time.sleep(delay)
        else:
            # No approved campaigns, check again in 2 minutes
            time.sleep(120)

if __name__ == "__main__":
    run_scheduler()
