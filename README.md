# 🚀 AI Outreach Agent

A fully autonomous, human-in-the-loop AI cold outreach system. This agent automates the process of researching companies, drafting highly personalized job application emails, intelligently selecting the right resume, and dispatching them at human-like intervals to avoid spam filters.

## ✨ Features

- **Dual LLM Architecture**: Uses Google Gemini (`gemini-1.5-flash-latest` / `gemini-3.6-flash`) for high-speed company research and drafting, with a seamless fallback to Meta's Open Source Llama 3 (`openai/gpt-oss-120b` via Groq) if rate limits are hit.
- **Human-in-the-loop UI**: A beautiful Streamlit dashboard that lets you easily manage your database, trigger bulk AI drafting, and manually edit/approve emails before they are sent.
- **Intelligent Resume Selection**: The AI analyzes the target company's industry and automatically attaches the most relevant PDF resume from your directory.
- **Anti-Spam Dispatcher**: 
  - Strictly operates during professional business hours (9:00 AM - 7:00 PM).
  - Implements randomized delays (3-10 minutes) between single emails.
  - Takes natural "lunch breaks" (25-50 minutes) after sending a batch of 8-15 emails.
- **Gmail API Integration**: Securely sends fully formatted, Rich HTML emails natively through your Google account using OAuth 2.0.

## 📁 Directory Structure

```text
ai_outreach_agent/
├── agents/                 # LLM logic for researching and drafting
├── contacts/               # Place your HR target list here (e.g., hr.xlsx)
├── database/               # Local SQLite database storing history & state
├── resumes/                # Place your PDF resumes here
├── services/               # Core logic (DB, Gmail OAuth, LLM routing)
├── app.py                  # The Streamlit Dashboard
├── scheduler.py            # The background email dispatcher
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md
```

## 🛠️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/ai-outreach-agent.git
cd ai-outreach-agent
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up Environment Variables**
Rename `.env.example` to `.env` and insert your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DAILY_EMAIL_LIMIT=40
```

**4. Add your data**
- Place your master Excel list of contacts inside the `contacts/` folder (e.g., `hr.xlsx`).
- Place your PDF resumes inside the `resumes/` folder.

**5. Set up Gmail OAuth**
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Enable the **Gmail API**.
- Create an **OAuth Consent Screen** (add your personal email as a Test User).
- Create **OAuth Client ID Credentials** (Application Type: Desktop App).
- Download the resulting JSON file, rename it exactly to `credentials.json`, and place it in the root of this project.

## 🚀 Usage

You operate the system using two separate tools:

### 1. The Workspace (Streamlit)
Whenever you want to work, open a terminal and run the dashboard:
```bash
python -m streamlit run app.py
```
- **Stats Tab**: View your daily limits and database health.
- **Prepare Drafts Tab**: Select a batch size and let the AI research companies and write drafts.
- **Review & Approve Tab**: Read the drafts, edit recipient emails (for testing), make tweaks, and click "Approve for Sending".

### 2. The Mailman (Scheduler)
In a separate terminal, run the background worker. You can leave this running all day.
```bash
python scheduler.py
```
*Note: The very first time you run this, a browser window will open asking you to log into your Google Account to authorize sending emails. After that, it will securely save a `token.json` file and run silently in the background.*

## 🔒 Security & Privacy
- **No data leaves your machine** except for the LLM API calls and the Gmail dispatch. Everything is stored locally in your SQLite database.
- Please ensure you do **not** commit your `.env`, `database/`, `credentials.json`, or `token.json` files to GitHub. A `.gitignore` has been provided to protect you.
