"""
One-time auth verification. Run this before starting app.py.

BEFORE RUNNING — Azure App Registration steps:
  1. Go to portal.azure.com → Azure Active Directory → App registrations → New registration
  2. Name: receipt-capture-local
  3. Supported account types: Accounts in this organizational directory only
  4. No redirect URI needed
  5. After creation, copy the Application (client) ID → AZURE_CLIENT_ID in .env
  6. Copy the Directory (tenant) ID → AZURE_TENANT_ID in .env
  7. Go to API permissions → Add permission → Microsoft Graph → Delegated → Mail.Read
  8. Grant admin consent (or ask your M365 admin)
  9. Your M365 account must have Full Access to bills@intellitax.co.uk

Then run:  python setup_auth.py
"""
import sys
sys.path.insert(0, ".")

import requests
import config
from worker.email.reader import get_token

print("Requesting token (you may need to authenticate in your browser)...")
token = get_token()
print("Token acquired.")

resp = requests.get(
    f"https://graph.microsoft.com/v1.0/users/{config.SHARED_MAILBOX}/mailFolders/inbox",
    headers={"Authorization": f"Bearer {token}"},
)

if resp.status_code == 200:
    data = resp.json()
    print(f"Inbox accessible: {data.get('totalItemCount', '?')} items, "
          f"{data.get('unreadItemCount', '?')} unread")
    print("Auth OK — ready to run app.py")
else:
    print(f"Inbox access failed: {resp.status_code}")
    print(resp.text)
    print("\nCommon causes:")
    print("  403 — Mail.Read permission not granted or no admin consent")
    print("  404 — SHARED_MAILBOX address wrong or account lacks Full Access")
    sys.exit(1)
