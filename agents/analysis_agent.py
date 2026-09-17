import sqlite3
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DB_PATH
from services.llm_service import generate_json_response

def analyze_company(company_name):
    """
    Checks the local cache for company info. If not found, uses the LLM service 
    to research the company and determine its industry and tech stack.
    """
    # 1. Check SQLite Cache
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT industry, summary, skills_required FROM company_cache WHERE company = ?", (company_name,))
    cached = cursor.fetchone()
    
    if cached:
        conn.close()
        print(f"[{company_name}] Loaded from cache.")
        return {
            "industry": cached[0],
            "summary": cached[1],
            "skills_required": cached[2]
        }
        
    # 2. If not cached, query LLM
    print(f"[{company_name}] Not in cache. Asking LLM...")
    system_prompt = "You are an expert tech recruiter and researcher."
    prompt = f"""
    Analyze the company '{company_name}'. 
    Provide a very short summary of what they do, their primary industry, and the likely technical skills they hire for (e.g., Python, GenAI, Data Science).
    
    Return ONLY a valid JSON object with this exact structure:
    {{
        "industry": "string",
        "summary": "string",
        "skills_required": "string"
    }}
    """
    
    result = generate_json_response(prompt, system_prompt)
    
    if result:
        # 3. Save to Cache for future use
        cursor.execute('''
            INSERT INTO company_cache (company, industry, summary, skills_required)
            VALUES (?, ?, ?, ?)
        ''', (company_name, result.get('industry', ''), result.get('summary', ''), result.get('skills_required', '')))
        conn.commit()
        
    conn.close()
    return result
