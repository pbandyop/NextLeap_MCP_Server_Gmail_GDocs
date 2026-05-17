# 🚀 Google Docs + Gmail MCP Server

A lightweight MCP-style server that integrates with Google Docs and Gmail.

This project demonstrates how to build **structured AI tool interfaces with approval gating**, inspired by the Model Context Protocol (MCP).

---

## ✨ Features

- 📄 Append structured content to Google Docs  
- 📧 Create Gmail drafts  
- 🔐 OAuth-based Google authentication  
- 🧠 MCP-style tool interface  
- ✅ Human-in-the-loop approval before execution  
- 🧩 Modular and extensible design  

---

## How to Use in Your Project

1. Run the MCP server:
   uvicorn server:app --reload

2. Call tools via API:
   POST /append_to_doc
   POST /create_email_draft

3. Integrate with your AI workflow:
   - Generate content using LLM
   - Send output to these endpoints

---
## 📁 Project Structure


```
google-mcp-server/
│── server.py
│── auth.py
│── docs_tool.py
│── gmail_tool.py
│── requirements.txt
│── credentials.json   (not committed)
│── token.json         (not committed)
│── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```
git clone <your-repo-url>
cd google-mcp-server
```

### 2. Create virtual environment

**macOS / Linux:**

```
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> On Windows, use `python` (not `python3`). The `python3` command often points to a Microsoft Store placeholder and fails with “Python was not found.”

###  3. Install dependencies

```
pip install -r requirements.txt
```

### 4. 🔑 Google API Setup

1. Go to Google Cloud Console
2. Create a new project
3. Enable:

   * Google Docs API
   * Gmail API
4. Configure OAuth Consent Screen
5. Create OAuth Credentials (Desktop App)
6. Download `credentials.json`
7. Place it in project root

---

### 5. 🔐 Run OAuth

**macOS / Linux:**

```
python3 auth.py
```

**Windows:**

```
python auth.py
```

Or double-click / run `auth.bat` from the project folder.

- Opens browser for login
- Generates token.json

### 6. ▶️ Run Server

```
uvicorn server:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## 🚂 Deploy to Railway

For production hosting (public HTTPS URL, no local terminal approval):

1. Complete local OAuth (`python auth.py`) so you have `token.json`.
2. Follow **[DEPLOYMENT.md](DEPLOYMENT.md)** — GitHub deploy, Railway variables, verification, and troubleshooting.

---

## 🧪 How to Test

### Append to Google Doc

Endpoint: `POST /append_to_doc`

Example:

```json
{
  "doc_id": "YOUR_DOC_ID",
  "content": "Hello from MCP 🚀"
}
```

---

### Create Email Draft

Endpoint: `POST /create_email_draft`

Example:

```json
{
  "to": "test@example.com",
  "subject": "Test Draft",
  "body": "This is a test email"
}
```


### 🔄 Workflow

```
Request → Approval → Tool Execution → Response
```

- Every action requires manual approval
- Ensures safe and controlled execution

### ⚠️ Important Notes

Do NOT commit:
- credentials.json
- token.json

Approval is CLI-based (terminal input)
Designed for local development

---

## ⚠️ Approval Flow

Every action requires manual approval in terminal:

```
ACTION: append_to_doc
PAYLOAD: {...}
Approve? (y/n):
```

Type:

```
y
```

---

## 🧠 MCP Design

This project demonstrates:

* Structured tool calls
* Separation of generation and execution
* Human approval before tool execution

---

## ❗ Notes

* No emails are sent automatically (draft only)
* Google Doc must have edit access
* Token is stored locally


---

## 📄 License

Apache License
