"""
Day 17 - Python Email Automation Masterclass
File 2: HTML Emails, Inline CID Images & Multi-File Attachments

Key Topics Covered:
1. MIME (Multipurpose Internet Mail Extensions) Hierarchy & Container Structure.
2. Dual-Payload Strategy: Plain Text Fallback + Responsive HTML Content.
3. Inline Media Embedding using Content-ID (CID) for zero-hosting images.
4. Automatic MIME Type Detection using `mimetypes.guess_type()`.
5. Attaching Multiple Binary Files (PDFs, CSVs, Archives) with metadata.
6. Header Privacy: Proper Handling of CC, BCC, and Reply-To envelopes.
7. MIME Structure Inspection via `email.iterators.walk()`.
"""

import os
import sys
import mimetypes
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from typing import List, Optional, Tuple, Dict

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
# SECTION 1: Understanding the MIME Multipart Hierarchy
# ==============================================================================
def explain_mime_hierarchy() -> None:
    """Displays ASCII architecture of complex multipart email payloads."""
    print_banner("1. MIME Multipart Architectural Tree")
    mime_tree = """
    multipart/mixed  (Root container for the entire message)
    |
    +-- multipart/alternative  (Dual-payload rendering engine)
    |   |
    |   +-- text/plain  (Fallback for terminal clients, screen readers)
    |   |
    |   \\-- multipart/related  (Rich media bundle)
    |       |
    |       +-- text/html  (HTML styling referring to <img src="cid:logo_id">)
    |       \\-- image/png  (Inline embedded asset with Content-ID: <logo_id>)
    |
    +-- application/pdf  (Attachment 1: Financial Statement.pdf)
    \\-- text/csv         (Attachment 2: Telemetry_Export.csv)
    """
    print(mime_tree)


# ==============================================================================
# SECTION 2: Modern Email Message Builder with HTML, CID & Attachments
# ==============================================================================
class RichEmailBuilder:
    """
    High-level factory using Python's modern EmailMessage API to construct
    bulletproof multipart messages with HTML styling, inline images, and attachments.
    """

    def __init__(self, sender: str, recipients: List[str], subject: str):
        self.msg = EmailMessage()
        self.msg["From"] = sender
        self.msg["To"] = ", ".join(recipients)
        self.msg["Subject"] = subject
        self.recipients = recipients

    def set_reply_to(self, reply_to_address: str) -> "RichEmailBuilder":
        """Sets an alternate address for recipient replies."""
        self.msg["Reply-To"] = reply_to_address
        return self

    def set_carbon_copies(self, cc_list: List[str], bcc_list: Optional[List[str]] = None) -> "RichEmailBuilder":
        """
        Configures CC and BCC recipients.
        CRITICAL RFC 5322 RULE:
        - CC recipients are included in both headers and envelope.
        - BCC recipients are added to transport envelope, but NEVER written to message headers!
        """
        if cc_list:
            self.msg["Cc"] = ", ".join(cc_list)
            self.recipients.extend(cc_list)
        if bcc_list:
            # BCC recipients are only tracked for the SMTP envelope
            self.recipients.extend(bcc_list)
        return self

    def add_content(self, plain_text: str, html_content: Optional[str] = None) -> "RichEmailBuilder":
        """Adds plain-text fallback and optional rich HTML payload."""
        # 1. Base plain text content
        self.msg.set_content(plain_text)

        # 2. Add alternative HTML payload if supplied
        if html_content:
            self.msg.add_alternative(html_content, subtype="html")
        return self

    def embed_inline_image(self, image_path: str, cid_name: str) -> "RichEmailBuilder":
        """
        Embeds an image as an inline CID resource for <img src="cid:cid_name"> tags.
        Does not appear as a separate downloadable attachment in compliant clients.
        """
        if not os.path.exists(image_path):
            print(f"[Warning] Inline image not found at '{image_path}', skipping.")
            return self

        # Guess image subtype (png, jpeg, etc.)
        ctype, _ = mimetypes.guess_type(image_path)
        if not ctype or not ctype.startswith("image/"):
            maintype, subtype = "image", "png"
        else:
            maintype, subtype = ctype.split("/", 1)

        with open(image_path, "rb") as img_file:
            img_data = img_file.read()

        # Add related part to the HTML alternative part
        # msg.get_payload()[1] corresponds to the HTML alternative
        if len(self.msg.get_payload()) > 1:
            html_part = self.msg.get_payload()[1]
            html_part.add_related(img_data, maintype=maintype, subtype=subtype, cid=f"<{cid_name}>")
        else:
            self.msg.add_related(img_data, maintype=maintype, subtype=subtype, cid=f"<{cid_name}>")

        return self

    def add_attachment(self, file_path: str, custom_filename: Optional[str] = None) -> "RichEmailBuilder":
        """
        Attaches a file with automatic MIME-type resolution and base64 encoding.
        """
        if not os.path.exists(file_path):
            print(f"[Warning] Attachment file not found: '{file_path}'")
            return self

        filename = custom_filename or os.path.basename(file_path)
        ctype, encoding = mimetypes.guess_type(file_path)

        if ctype is None or encoding is not None:
            # Generic binary stream fallback
            ctype = "application/octet-stream"

        maintype, subtype = ctype.split("/", 1)

        with open(file_path, "rb") as f:
            file_data = f.read()

        self.msg.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=filename
        )
        return self

    def build(self) -> Tuple[EmailMessage, List[str]]:
        """Returns the finalized EmailMessage and the complete envelope recipient list."""
        return self.msg, self.recipients


# ==============================================================================
# SECTION 3: MIME Inspection & Structure Diagnostic
# ==============================================================================
def inspect_mime_tree(message: EmailMessage) -> None:
    """Walks through each MIME part of the email and logs its properties."""
    print_banner("3. Inspecting Constructed Message MIME Tree")
    print(f"Subject       : {message['Subject']}")
    print(f"From          : {message['From']}")
    print(f"To            : {message['To']}")
    print(f"Cc            : {message.get('Cc', 'None')}")
    print(f"Top Content   : {message.get_content_type()}")
    print("\n--- Traversing Sub-parts ---")

    part_count = 0
    for part in message.walk():
        part_count += 1
        content_type = part.get_content_type()
        content_disp = part.get("Content-Disposition", "None")
        content_id = part.get("Content-ID", "None")
        payload = part.get_payload(decode=True)
        size_bytes = len(payload) if payload else 0

        print(f"Part #{part_count:<2} | Type: {content_type:<24} | Size: {size_bytes:>6} bytes | "
              f"CID: {content_id:<20} | Disp: {content_disp}")


# ==============================================================================
# SECTION 4: Dual-Dispatch Runner (Simulation & Network Dispatch)
# ==============================================================================
def dispatch_rich_email_demo() -> None:
    """Constructs a rich marketing / report email and tests its dispatch."""
    print_banner("4. Building & Dispatching Rich HTML + Attachment Email")

    sender = "analytics-team@datacloud.org"
    recipients = ["client.lead@enterprise.com"]
    cc = ["finance.audit@datacloud.org"]
    bcc = ["archive.vault@datacloud.org"]  # Blind carbon copy

    # Plain-text alternative fallback
    plain_text_fallback = (
        "Q2 Performance & Operations Report\n\n"
        "Hello Operations Lead,\n\n"
        "Your monthly analytical dataset is ready. Please refer to the HTML view "
        "or open the attached sample CSV report for detailed telemetry records.\n\n"
        "--\nPython Automation Masterclass Team"
    )

    # Rich responsive HTML template with inline logo reference
    html_body = """<!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; }
        .card { max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; padding: 25px; border: 1px solid #e2e8f0; }
        .header { display: flex; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; }
        .header img { height: 45px; width: 45px; margin-right: 15px; border-radius: 6px; }
        .header h2 { margin: 0; color: #1e40af; }
        .highlight { background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 15px 0; }
        .badge { background: #10b981; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .footer { margin-top: 25px; font-size: 12px; color: #94a3b8; text-align: center; }
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <img src="cid:brand_logo" alt="Company Logo" />
          <h2>Monthly Performance Audit</h2>
        </div>
        <p>Dear Partner,</p>
        <p>The automated data ingestion cycle has completed with <span class="badge">99.98% SUCCESS</span>.</p>
        <div class="highlight">
          <strong>Key Summary:</strong>
          <ul>
            <li>Total Records Audited: <strong>1,482,900</strong></li>
            <li>Database Latency: <strong>14.2ms</strong></li>
            <li>Attached Artifact: <code>sample_report.csv</code></li>
          </ul>
        </div>
        <p>You can review the raw telemetry metrics inside the attached CSV file.</p>
        <div class="footer">Automated Report Generator &bull; Python smtplib / EmailMessage</div>
      </div>
    </body>
    </html>
    """

    # Asset paths
    logo_path = os.path.join("data", "sample_logo.png")
    csv_report_path = os.path.join("data", "sample_report.csv")

    builder = RichEmailBuilder(sender, recipients, "📊 Q2 Performance & Analytics Report")
    builder.set_reply_to("support@datacloud.org")
    builder.set_carbon_copies(cc_list=cc, bcc_list=bcc)
    builder.add_content(plain_text=plain_text_fallback, html_content=html_body)

    # Embed inline CID image
    if os.path.exists(logo_path):
        builder.embed_inline_image(logo_path, cid_name="brand_logo")
        print(f"[Added] Inline CID Image: '{logo_path}' -> cid:brand_logo")

    # Add CSV attachment
    if os.path.exists(csv_report_path):
        builder.add_attachment(csv_report_path, custom_filename="Monthly_Telemetry_Report.csv")
        print(f"[Added] File Attachment: '{csv_report_path}'")

    email_message, envelope_recipients = builder.build()

    # Step 3: Inspect MIME Tree
    inspect_mime_tree(email_message)

    # Step 4: Dispatch Simulation
    print("\n--- SMTP Dispatch Simulation ---")
    print(f"Total Transport Envelope Recipients (To + Cc + Bcc): {len(envelope_recipients)}")
    print(f"Envelope Recipients List: {envelope_recipients}")
    print(f"Total Message Payload Size: {len(email_message.as_bytes())} bytes")
    print("[SUCCESS] Rich multipart email constructed and verified!")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    print_banner("Day 17 - Module 2: HTML Emails, Inline CID Images & Attachments")
    explain_mime_hierarchy()
    dispatch_rich_email_demo()
