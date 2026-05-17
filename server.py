import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

# ---------------- LOGGING SETUP ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _materialize_credentials_from_env() -> bool:
    """Write credentials.json from GOOGLE_CREDENTIALS_JSON (Railway / Render)."""
    raw = _env("GOOGLE_CREDENTIALS_JSON")
    if not raw:
        return False
    with open("credentials.json", "w", encoding="utf-8") as f:
        f.write(raw)
    logger.info("credentials.json created from GOOGLE_CREDENTIALS_JSON")
    return True


_credentials_materialized = _materialize_credentials_from_env()
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
    logger.info(
        "Deploy config: GOOGLE_CREDENTIALS_JSON=%s, GOOGLE_TOKEN_JSON=%s, credentials.json=%s",
        "set" if _env("GOOGLE_CREDENTIALS_JSON") else "missing",
        "set" if _env("GOOGLE_TOKEN_JSON") else "missing",
        "exists" if os.path.exists("credentials.json") else "missing",
    )

# ---------------- APP INIT ---------------- #
app = FastAPI(title="Google MCP Server")


# ---------------- REQUEST SCHEMAS ---------------- #
class AppendDocInput(BaseModel):
    doc_id: str
    content: str


class EmailInput(BaseModel):
    to: str 
    subject: str
    body: str


# ---------------- APPROVAL LAYER ---------------- #
def approve(action: str, payload: dict) -> bool:
    """
    Approval system:
    - Local → manual approval
    - Deployment → auto-approved
    """

    # ✅ Auto-approve in deployment (set AUTO_APPROVE=true in Render/Railway/etc.)
    if (
        os.getenv("AUTO_APPROVE", "false").lower() == "true"
        or os.getenv("RENDER")
        or os.getenv("RAILWAY_ENVIRONMENT")
    ):
        logger.info(f"{action} auto-approved (deployment env)")
        return True

    # 🧪 Local CLI approval
    try:
        print("\n-----------------------------")
        print(f"ACTION: {action}")
        print(f"PAYLOAD: {payload}")
        print("-----------------------------")

        decision = input("Approve? (y/n): ").strip().lower()

        if decision == "y":
            logger.info(f"{action} approved")
            return True
        else:
            logger.warning(f"{action} rejected")
            return False

    except Exception as e:
        logger.error(f"Approval error: {e}")
        return False


# ---------------- MCP TOOL LIST ---------------- #
@app.get("/tools")
def list_tools():
    return [
        {
            "name": "append_to_doc",
            "description": "Append content to Google Doc"
        },
        {
            "name": "create_email_draft",
            "description": "Create Gmail draft"
        }
    ]


# ---------------- DOC TOOL ---------------- #
@app.post("/append_to_doc")
def run_append(data: AppendDocInput):
    try:
        logger.info("Received request for append_to_doc")

        if not approve("append_to_doc", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        result = append_to_doc(
            doc_id=data.doc_id,
            content=data.content
        )

        logger.info("append_to_doc executed successfully")

        return result

    except Exception as e:
        logger.error(f"Error in append_to_doc: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- EMAIL TOOL ---------------- #
@app.post("/create_email_draft")
def run_email(data: EmailInput):
    try:
        logger.info("Received request for create_email_draft")

        if not approve("create_email_draft", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        result = create_email_draft(
            to=data.to,
            subject=data.subject,
            body=data.body
        )

        logger.info("create_email_draft executed successfully")

        return result

    except Exception as e:
        logger.error(f"Error in create_email_draft: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- HEALTH CHECK ---------------- #
def _config_status() -> dict:
    creds_env = _env("GOOGLE_CREDENTIALS_JSON")
    token_env = _env("GOOGLE_TOKEN_JSON")

    if creds_env and not os.path.exists("credentials.json"):
        _materialize_credentials_from_env()

    credentials_ready = os.path.exists("credentials.json")
    token_configured = bool(token_env) or os.path.exists("token.json")

    return {
        "message": "Google MCP Server is running 🚀",
        "deployed": bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER")),
        "credentials_ready": credentials_ready,
        "token_configured": token_configured,
        # Safe diagnostics (no secret values) — use to debug Railway variables
        "config": {
            "GOOGLE_CREDENTIALS_JSON": "set" if creds_env else "missing",
            "GOOGLE_TOKEN_JSON": "set" if token_env else "missing",
            "AUTO_APPROVE": os.getenv("AUTO_APPROVE", "not set"),
        },
    }


@app.get("/")
def root():
    return _config_status()