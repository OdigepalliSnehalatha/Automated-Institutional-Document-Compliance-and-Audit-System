# n8n Realistic OTP Generation & Email Automation

This module connects the **Automated Institutional Document Compliance and Audit System** with **n8n** to deliver realistic, automated one-time passcodes (OTP) directly to users' email addresses.

---

## 🏗️ Architecture & Workflow Overview

```
[User Enters Email in Portal]
              │
              ▼
[FastAPI Backend: /login or /register]
  • Generates cryptographically secure 6-digit OTP
  • Computes SHA-256 hash & stores in PostgreSQL (`login_otps`)
  • Sets strict 5-minute expiry & max 5 attempt limit
              │
              ▼ (HTTP POST Webhook)
[n8n Automation Engine / Webhook]
  Endpoint: http://localhost:5678/webhook/send-otp
              │
              ├─► Node 1: Webhook Trigger (Receives email, otp, institution, role)
              ├─► Node 2: Code Node (Generates sleek Institutional HTML Email)
              ├─► Node 3: Send Email Node (Dispatches email to user via Gmail/SMTP)
              └─► Node 4: Respond to Webhook (Returns success status to FastAPI)
              │
              ▼
[User Checks Email Inbox & Enters 6-Digit Code]
              │
              ▼
[FastAPI Validates Hash & Grants Session Access]
```

---

## 📁 Files Included

| File | Description |
| :--- | :--- |
| **`institutional_otp_workflow.json`** | Ready-to-import n8n workflow file containing Webhook, HTML Generator, Email Dispatcher, and Response nodes. |
| **`local_n8n_bridge.py`** | Standalone Python webhook bridge emulating n8n on port `5678` with direct email sending & terminal logging. |
| **`start_n8n_bridge.bat`** | One-click Windows batch script to launch the local n8n bridge. |

---

## 🚀 Setup Instructions

### Option 1: Using Real n8n (Desktop, Docker, or Cloud)

1. **Start n8n**:
   - If running locally: `npx n8n`
   - Access n8n at `http://localhost:5678`
2. **Import Workflow**:
   - In n8n, click **Workflows** → **Import from File...**
   - Select `n8n/institutional_otp_workflow.json`
3. **Configure Email Node**:
   - Double-click the **Send Email via SMTP / Mail Service** node (or replace with the **Gmail** node).
   - Add your SMTP credentials or connect your Google/Gmail account via OAuth2.
4. **Activate Workflow**:
   - Toggle the workflow switch to **Active**.
5. **Update `.env`**:
   Ensure `N8N_WEBHOOK_URL` matches your n8n webhook URL:
   ```env
   N8N_ENABLED=true
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/send-otp
   DEV_EXPOSE_OTP=false
   ```

---

### Option 2: Using the Lightweight Local n8n Bridge

If you want to test the entire webhook flow without installing n8n:
1. Double-click `n8n/start_n8n_bridge.bat` (or run `python n8n/local_n8n_bridge.py`).
2. The bridge listens on `http://127.0.0.1:5678/webhook/send-otp`.
3. When you submit your email in the portal, the bridge receives the payload, logs the event, sends the email (if SMTP is configured in `.env`), and responds with standard n8n JSON.

---

## 🔒 Security & Realistic Delivery Features

- **No OTP Leakage:** With `DEV_EXPOSE_OTP=false`, the OTP is **never** included in the HTTP response or stored in localStorage. The user must check their real email.
- **SHA-256 Hashed Storage:** Passcodes are never stored in plaintext in the database.
- **5-Minute Expiry:** Codes automatically expire after 5 minutes.
- **Max Attempt Limit:** After 5 incorrect entries, the passcode is immediately invalidated.
- **Graceful Fallback:** If n8n or the webhook is temporarily offline, the backend logs a notice and ensures institutional audits and logins continue without interruption.
