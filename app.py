import streamlit as st
import sqlite3
import pandas as pd
import time
import os

from services.db_service import DB_PATH
from agents.analysis_agent import analyze_company
from agents.email_agent import draft_email_and_select_resume

from config import DAILY_EMAIL_LIMIT

st.set_page_config(page_title="AI Outreach Agent", page_icon="🎯", layout="wide")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {}
    
    # Global stats
    for status in ['pending', 'drafted', 'failed']:
        cursor.execute(f"SELECT COUNT(*) FROM contacts WHERE status = '{status}'")
        stats[status] = cursor.fetchone()[0]
        
    # Today's sent specifically
    cursor.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'sent' AND date(sent_at) = date('now', 'localtime')")
    stats['sent_today'] = cursor.fetchone()[0]
    
    # Total sent all time
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE status = 'sent'")
    stats['sent_total'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

st.title("🎯 Agentic AI Job Outreach")

tab1, tab2, tab3 = st.tabs(["📊 Overview", "⚙️ Prepare Drafts", "✅ Review & Approve"])

# --- TAB 1: OVERVIEW ---
with tab1:
    st.header("Today's Progress")
    stats = fetch_stats()
    
    target = DAILY_EMAIL_LIMIT
    completion = min(stats['sent_today'] / target, 1.0) if target > 0 else 0
    
    st.progress(completion, text=f"Completion: {int(completion * 100)}%")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Today's Sent", f"{stats['sent_today']} / {target}")
    col2.metric("Total Pending", stats['pending'])
    col3.metric("Drafts to Review", stats['drafted'])
    col4.metric("Failed", stats['failed'])
    col5.metric("Total All-Time Sent", stats['sent_total'])
    
    st.info("💡 Note: 'Replies' tracking requires advanced Gmail Webhooks, which is not included in this MVP. Check your Gmail inbox manually for responses!")

# --- TAB 2: PREPARE DRAFTS ---
with tab2:
    st.header("Generate AI Emails")
    st.write("This will use Gemini/Groq to research pending companies and write personalized emails.")
    
    batch_size = st.number_input("How many emails to draft?", min_value=1, max_value=50, value=5)
    
    if st.button("Start AI Drafting"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE status = 'pending' LIMIT ?", (batch_size,))
        pending_contacts = cursor.fetchall()
        
        if not pending_contacts:
            st.warning("No pending contacts found!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, contact in enumerate(pending_contacts):
                company = contact['company']
                hr_name = contact['name']
                cid = contact['id']
                
                status_text.text(f"Researching {company}...")
                
                # 1. Analyze Company
                analysis = analyze_company(company)
                if not analysis:
                    st.error(f"Failed to analyze {company}. Check API keys.")
                    continue
                    
                status_text.text(f"Drafting email for {hr_name} at {company}...")
                
                # 2. Draft Email
                draft = draft_email_and_select_resume(cid, hr_name, company, analysis)
                
                progress_bar.progress((i + 1) / len(pending_contacts))
                
            status_text.text("Drafting complete! Go to the 'Review' tab.")
            st.success("Batch processed successfully!")
        conn.close()

# --- TAB 3: REVIEW & APPROVE ---
with tab3:
    st.header("Review Drafted Emails")
    st.write("Review the AI's work, make manual edits, and approve them for sending.")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id as cid, c.company, c.name, c.email, camp.id as camp_id, camp.subject, camp.body_draft, camp.resume_used
        FROM contacts c
        JOIN campaigns camp ON c.id = camp.contact_id
        WHERE c.status = 'drafted'
    ''')
    drafts = cursor.fetchall()
    
    if not drafts:
        st.info("No drafts currently awaiting review. Go to 'Prepare Drafts' to generate some.")
    else:
        for draft in drafts:
            with st.expander(f"✉️ To: {draft['name']} @ {draft['company']}"):
                with st.form(key=f"form_{draft['cid']}"):
                    edited_email = st.text_input("Recipient Email (Change this to your own email to test!)", value=draft['email'])
                    st.write(f"**AI Selected Resume:** `{draft['resume_used']}`")
                    
                    edited_subject = st.text_input("Subject", value=draft['subject'])
                    edited_body = st.text_area("Body", value=draft['body_draft'], height=300)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("✅ Approve for Sending"):
                            # Update DB
                            update_cursor = conn.cursor()
                            update_cursor.execute('''
                                UPDATE campaigns SET subject=?, body_draft=?, status='approved' WHERE id=?
                            ''', (edited_subject, edited_body, draft['camp_id']))
                            update_cursor.execute("UPDATE contacts SET status='approved', email=? WHERE id=?", (edited_email, draft['cid']))
                            conn.commit()
                            st.success("Approved! Refresh page to see next drafts.")
                    with col2:
                        if st.form_submit_button("❌ Reject / Delete"):
                            update_cursor = conn.cursor()
                            update_cursor.execute("DELETE FROM campaigns WHERE id=?", (draft['camp_id'],))
                            update_cursor.execute("UPDATE contacts SET status='pending' WHERE id=?", (draft['cid'],))
                            conn.commit()
                            st.warning("Rejected. Sent back to pending queue.")
    conn.close()
