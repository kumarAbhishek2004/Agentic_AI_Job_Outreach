import os
import sqlite3
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DB_PATH
from services.llm_service import generate_json_response

def get_available_resumes():
    """Reads the names of the PDF files in the resumes directory."""
    resume_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resumes')
    try:
        return [f for f in os.listdir(resume_dir) if f.endswith('.pdf')]
    except Exception:
        return []

def draft_email_and_select_resume(contact_id, hr_name, company_name, company_analysis):
    """
    Uses the LLM service to draft a highly personalized email and select the best matching resume.
    Saves the draft to the database.
    """
    available_resumes = get_available_resumes()
    
    system_prompt = "You are an expert AI Engineer applying for a job."
    prompt = f"""
    You are an expert AI outreach assistant. Your job is to select the best resume and format a specific cold outreach email to {hr_name} at {company_name}.
    
    Company Context:
    - Industry: {company_analysis.get('industry', 'Technology')}
    - What they do: {company_analysis.get('summary', '')}
    
    Available Resumes (PDF filenames):
    {available_resumes}
    
    CRITICAL INSTRUCTION: You MUST use the EXACT email template below. Do not deviate from the structure, do not change the wording, do not remove the links. 
    Only replace the placeholders [HR Name] with "{hr_name}" and [Company Name] with "{company_name}".
    
    --- TEMPLATE START ---
    Hi [HR Name],
    
    I hope you're doing well.
    
    I came across your profile while exploring opportunities at [Company Name].
    
    I'm a final-year B.Tech student at IIIT Una with hands-on experience in Generative AI, Machine Learning, and Deep Learning. I've built production-grade AI applications, including LLM-powered systems, RAG-based applications, MCP servers, and AI workflow automation, along with experience in FastAPI, API integrations, and model development. I've attached my resume for your reference. You can also explore my work here:
    GitHub: https://github.com/kumarAbhishek2004
    Portfolio: https://my-portfolio-zeta-orpin-72.vercel.app/
    
    I'm currently looking for internship and full-time opportunities in Generative AI, AI/ML, Machine Learning, Deep Learning, or Software Engineering. If there are any suitable openings at [Company Name], I'd be grateful if you could consider my profile.
    
    I have attached my resume for your consideration. I would be grateful for the opportunity to discuss how my skills and experience can contribute to your team.
    Thank you for your time and consideration. I look forward to hearing from you.
    
    Best regards,
    Kumar Abhishek
    9608013812
    abhishekkumar.ch2607@gmail.com
    --- TEMPLATE END ---
    
    Select the SINGLE most relevant resume filename from the list provided based on the company's industry.
    
    Return ONLY a valid JSON object with this exact structure:
    {{
        "subject": "Application for Generative AI / ML Opportunities at {company_name}",
        "body": "<Insert the complete, exact template with the names filled in here>",
        "selected_resume": "filename.pdf"
    }}
    """
    
    result = generate_json_response(prompt, system_prompt)
    
    if result:
        # Save the drafted email to the campaigns table
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaigns (contact_id, status, subject, body_draft, resume_used)
            VALUES (?, 'drafted', ?, ?, ?)
        ''', (contact_id, result.get('subject', ''), result.get('body', ''), result.get('selected_resume', '')))
        
        # Update contact status to drafted
        cursor.execute('''
            UPDATE contacts SET status = 'drafted' WHERE id = ?
        ''', (contact_id,))
        
        conn.commit()
        conn.close()
        
        print(f"[{company_name}] Successfully drafted email and selected {result.get('selected_resume')}")
        return result
    else:
        print(f"[{company_name}] Failed to draft email.")
        return None
