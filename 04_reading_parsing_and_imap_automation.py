"""
Day 17 - Python Email Automation Masterclass
File 4: Reading Emails, Parsing RFC 822 Payloads & IMAP Automation

Key Topics Covered:
1. Receiving Protocols: IMAP (Port 993) vs POP3 (Port 995) vs SMTP (Port 587).
2. Connecting with `imaplib.IMAP4_SSL` and Mailbox Folder Traversal.
3. Advanced Search Queries (`UNSEEN`, `FROM`, `SUBJECT`, Date ranges).
4. Parsing Raw MIME Payloads using modern `email.message_from_bytes()`.
5. Decoding RFC 2047 Multilingual Headers (`email.header.decode_header`).
6. Automated Attachment Extraction & Directory Harvesting with SHA-256 Validation.
7. Mailbox Flag Mutations (`\\Seen`, `\\Flagged`, `\\Deleted`, `expunge`).
8. Dual Execution Modes: Offline RFC 822 Simulation & Live IMAP SSL Connection.
"""

import os
import sys
import ssl
import email
import hashlib
import imaplib
import datetime
from email.header import decode_header
from email.message import EmailMessage
from typing import List, Dict, Any, Optional, Tuple

# Ensure robust stdout encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner(title: str) -> None:
    """Helper to display formatted section headers."""
    print(f"\n{'=' * 75}\n# {title}\n{'=' * 75}")


# ==============================================================================
# SECTION 1: IMAP vs POP3 vs SMTP Comparison Matrix
# ==============================================================================
def explain_email_protocols() -> None:
    """Displays comparative breakdown of email communication protocols."""
    print_banner("1. Protocol Breakdown: IMAP vs POP3 vs SMTP")
    comparison = """
    +----------+----------+----------+-----------------------------------------------+
    | Protocol | Port     | Role     | State & Synchronization Behavior              |
    +----------+----------+----------+-----------------------------------------------+
    | SMTP     | 587/465  | PUSH/Send| Outbound delivery from client to mail server. |
    | IMAP     | 993(SSL) | PULL/Read| 2-Way Sync. Messages remain on server. Folder |
    |          |          |          | hierarchy & flags (\\Seen, \\Starred) synced.  |
    | POP3     | 995(SSL) | PULL/Read| 1-Way Download. Typically downloads locally  |
    |          |          |          | and deletes from server. No folder sync.     |
    +----------+----------+----------+-----------------------------------------------+
    """
    print(comparison)


# ==============================================================================
# SECTION 2: Header Decoding & String Normalization
# ==============================================================================
def decode_mime_header(header_value: Optional[str]) -> str:
    """
    Decodes RFC 2047 encoded header strings (e.g. '=?utf-8?b?...=?') into standard Python strings.
    """
    if not header_value:
        return ""

    decoded_fragments = decode_header(header_value)
    result_parts = []

    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            encoding = charset or "utf-8"
            try:
                result_parts.append(fragment.decode(encoding, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result_parts.append(fragment.decode("utf-8", errors="replace"))
        else:
            result_parts.append(str(fragment))

    return "".join(result_parts)


# ==============================================================================
# SECTION 3: MIME Parser & Attachment Harvester
# ==============================================================================
class EmailMessageParser:
    """
    High-level parser that converts raw RFC 822 email byte streams into
    structured Python dictionary records with automated attachment harvesting.
    """
    @staticmethod
    def parse_raw_bytes(raw_bytes: bytes, download_dir: Optional[str] = None) -> Dict[str, Any]:
        """Parses raw email bytes into structured metadata, body text, and attachments."""
        msg = email.message_from_bytes(raw_bytes)

        subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
        sender = decode_mime_header(msg.get("From", "(Unknown Sender)"))
        to_recipients = decode_mime_header(msg.get("To", ""))
        date_str = msg.get("Date", "")
        message_id = msg.get("Message-ID", "")

        plain_body_parts: List[str] = []
        html_body_parts: List[str] = []
        attachments_meta: List[Dict[str, Any]] = []

        # Walk through all MIME payload sections
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()

            # Attachment detection
            if "attachment" in content_disposition.lower() or filename:
                decoded_filename = decode_mime_header(filename) if filename else f"attachment_{len(attachments_meta) + 1}.bin"
                # Sanitize filename against directory traversal attacks
                safe_filename = os.path.basename(decoded_filename).replace(" ", "_")
                
                payload = part.get_payload(decode=True)
                if payload:
                    sha256_hash = hashlib.sha256(payload).hexdigest()
                    size_bytes = len(payload)

                    saved_path = None
                    if download_dir:
                        os.makedirs(download_dir, exist_ok=True)
                        saved_path = os.path.join(download_dir, safe_filename)
                        with open(saved_path, "wb") as f:
                            f.write(payload)

                    attachments_meta.append({
                        "filename": safe_filename,
                        "size_bytes": size_bytes,
                        "content_type": content_type,
                        "sha256": sha256_hash,
                        "saved_to": saved_path
                    })
                continue

            # Text / HTML body extraction
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    plain_body_parts.append(payload.decode(charset, errors="replace"))

            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html_body_parts.append(payload.decode(charset, errors="replace"))

        return {
            "subject": subject,
            "sender": sender,
            "to": to_recipients,
            "date": date_str,
            "message_id": message_id,
            "plain_body": "\n".join(plain_body_parts).strip(),
            "html_body": "\n".join(html_body_parts).strip(),
            "attachments": attachments_meta
        }


# ==============================================================================
# SECTION 4: IMAP Automation Engine (Live & Offline Simulation)
# ==============================================================================
class IMAPAutomationClient:
    """
    Automates inbox monitoring, message querying, and attachment harvesting.
    """
    def __init__(self, host: str = "imap.gmail.com", port: int = 993, is_simulation: bool = True):
        self.host = host
        self.port = port
        self.is_simulation = is_simulation

    def search_and_harvest(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        mailbox: str = "INBOX",
        search_criterion: str = "UNSEEN",
        download_dir: str = "downloaded_attachments"
    ) -> List[Dict[str, Any]]:
        """Searches mailbox matching criteria and extracts messages and attachments."""
        if self.is_simulation or not (username and password):
            print(f"[IMAP Simulator] Simulating connection to {self.host}:{self.port} over SSL...")
            return self._simulate_harvest(mailbox, search_criterion, download_dir)

        # Live IMAP Connection
        print(f"[IMAP] Connecting to {self.host}:{self.port} with SSL...")
        results = []
        try:
            ssl_context = ssl.create_default_context()
            with imaplib.IMAP4_SSL(self.host, self.port, ssl_context=ssl_context) as client:
                client.login(username, password)
                print(f"[IMAP] Logged in as {username}. Selecting mailbox '{mailbox}'...")
                
                # Select mailbox in Read/Write mode
                status, _ = client.select(mailbox)
                if status != "OK":
                    print(f"[IMAP Error] Failed to select mailbox '{mailbox}'")
                    return []

                # Execute search query
                print(f"[IMAP] Searching for criterion: {search_criterion}...")
                status, search_data = client.search(None, search_criterion)
                if status != "OK":
                    print("[IMAP Error] Search query failed.")
                    return []

                message_ids = search_data[0].split()
                print(f"[IMAP] Found {len(message_ids)} matching messages.")

                for msg_id in message_ids:
                    # Fetch RFC822 raw message bytes
                    status, msg_data = client.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            raw_email = response_part[1]
                            parsed = EmailMessageParser.parse_raw_bytes(raw_email, download_dir)
                            results.append(parsed)

                            # Mark message as read
                            client.store(msg_id, "+FLAGS", "\\Seen")

            return results
        except Exception as e:
            print(f"[IMAP Connection Error] {e}")
            return []

    def _simulate_harvest(self, mailbox: str, search_criterion: str, download_dir: str) -> List[Dict[str, Any]]:
        """Simulates incoming email stream with attachments for offline execution."""
        print(f">> Selected Mailbox: {mailbox} (Status: OK, 12 Total Messages)")
        print(f">> Executing Query : SEARCH {search_criterion} -> [Found 2 Unread Matches]")

        # Create simulated RFC 822 messages
        simulated_messages = []

        # Simulated Message 1: Monthly Invoice
        msg1 = EmailMessage()
        msg1["Subject"] = "🧾 Invoice Receipt #INV-98214 - Cloud Services"
        msg1["From"] = "Billing Department <billing@cloudprovider.local>"
        msg1["To"] = "Operations Lead <ops@client.com>"
        msg1["Date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg1.set_content("Hello,\n\nPlease find attached your monthly cloud compute invoice.")
        # Attach sample invoice
        invoice_sample_bytes = b"INVOICE_ID,AMOUNT,STATUS\nINV-98214,249.00,PAID\n"
        msg1.add_attachment(
            invoice_sample_bytes,
            maintype="text",
            subtype="csv",
            filename="invoice_INV-98214.csv"
        )
        simulated_messages.append(msg1.as_bytes())

        # Simulated Message 2: Security Alert
        msg2 = EmailMessage()
        msg2["Subject"] = "🚨 Security Alert: New Login from New IP"
        msg2["From"] = "Security Center <security@authservice.local>"
        msg2["To"] = "User <ops@client.com>"
        msg2["Date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg2.set_content("We detected a successful SSH key authentication from IP: 198.51.100.42.")
        simulated_messages.append(msg2.as_bytes())

        parsed_records = []
        for idx, raw_bytes in enumerate(simulated_messages, start=1):
            parsed = EmailMessageParser.parse_raw_bytes(raw_bytes, download_dir)
            parsed_records.append(parsed)
            print(f">> Fetched Msg #{idx} | Subject: '{parsed['subject']}' | Flags: Marked \\Seen")

        return parsed_records


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    print_banner("Day 17 - Module 4: Reading Emails & IMAP Automation")

    # 1. Explain protocol landscape
    explain_email_protocols()

    # 2. Run IMAP inbox scanner & attachment extractor
    print_banner("2. Executing IMAP Inbox Watchdog & Harvester")
    client = IMAPAutomationClient(is_simulation=True)

    download_folder = os.path.join("downloaded_attachments")
    extracted_emails = client.search_and_harvest(
        mailbox="INBOX",
        search_criterion="UNSEEN",
        download_dir=download_folder
    )

    # 3. Display Parsed Results
    print_banner("3. Parsed Email Payloads & Harvested Artifacts")
    for idx, email_data in enumerate(extracted_emails, start=1):
        print(f"\n[Message #{idx}]")
        print(f"  - Subject     : {email_data['subject']}")
        print(f"  - From        : {email_data['sender']}")
        print(f"  - Date        : {email_data['date']}")
        print(f"  - Plain Body  : {email_data['plain_body'][:120]}...")
        print(f"  - Attachments : {len(email_data['attachments'])}")
        for att in email_data["attachments"]:
            print(f"      * Filename : {att['filename']} ({att['size_bytes']} bytes)")
            print(f"        Saved To : {att['saved_to']}")
            print(f"        SHA-256  : {att['sha256'][:16]}...")

    print("\n[SUCCESS] IMAP message parsing and attachment harvesting demonstrated successfully!")
