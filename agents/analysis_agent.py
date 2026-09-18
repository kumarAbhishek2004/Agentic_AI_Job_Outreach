import sqlite3
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DB_PATH
from services.llm_service import generate_json_response

def perform_web_search(company_name):
    """Searches DuckDuckGo for the company's tech stack and careers."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            # Search specifically for tech stack, engineering, or AI careers
            results = ddgs.text(f"{company_name} company software engineering tech stack careers", max_results=3)
            if results:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        print(f"Web search failed for {company_name}: {e}")
    return "No recent web data available."

def analyze_company(company_name):
    """
    Checks the local cache for company info. If not found, actively searches the web
    and uses the LLM service to determine its industry and tech stack.
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
        
    # 2. If not cached, perform LIVE WEB SEARCH
    print(f"[{company_name}] Not in cache. Performing LIVE WEB SEARCH...")
    web_data = perform_web_search(company_name)
    
    print(f"[{company_name}] Web search complete. Asking LLM to analyze live data...")
    system_prompt = "You are an expert tech recruiter and researcher."
    prompt = f"""
    Analyze the company '{company_name}'. 
    
    Here is the live web search data we just found about them:
    {web_data}
    
    Based on this live data (or your internal knowledge if the data is sparse), provide a very short summary of what they do, their primary industry, and the exact technical skills or roles they are likely hiring for (e.g., Python, GenAI, Data Science, React).
    
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
