"""
Day 17 - Python Email Automation Masterclass
File 1: SMTP Fundamentals, Security Protocols & Plain Text Automation

Key Topics Covered:
1. Understanding the SMTP (Simple Mail Transfer Protocol) Lifecycle & Handshake.
2. Security Protocols: Port 587 (STARTTLS) vs Port 465 (SSL/TLS) vs Port 25 (Unencrypted).
3. Modern Python 3.6+ `email.message.EmailMessage` vs Legacy `email.mime.text.MIMEText`.
4. Environment Variables & Secure Credential Handling (Google App Passwords vs Plain Auth).
5. Robust Exception Handling (Authentication, Network Timeouts, Recipient Refusals).
6. Dual Execution Modes: Live SMTP Execution & Offline Simulation Mode.
"""

import os
import sys
import ssl
import socket
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

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
# SECTION 1: SMTP Architecture & Protocol Fundamentals
# ==============================================================================
def explain_smtp_lifecycle() -> None:
    """Explains the underlying SMTP handshake commands exchanged over TCP."""
    print_banner("1. SMTP Protocol Handshake Lifecycle")
    lifecycle_diagram = """
    CLIENT (Python smtplib)                          SMTP SERVER (e.g. Gmail / Postfix)
    -----------------------                          ----------------------------------
    1. Connect TCP (Port 587)        ==============>  220 smtp.gmail.com ESMTP ready
    2. EHLO client.local             ==============>  250-smtp.gmail.com welcomes you
                                                      250-STARTTLS (supported extension)
    3. STARTTLS                      ==============>  220 2.0.0 Ready to start TLS
       [TLS Handshake negotiation & certificate verification occurs]
    4. EHLO client.local (Encrypted) ===============>  250-AUTH LOGIN PLAIN
    5. AUTH LOGIN (Base64 User/Pass) ===============>  235 2.7.0 Authentication successful
    6. MAIL FROM: <sender@mail.com>  ==============>  250 2.1.0 Sender OK
    7. RCPT TO: <dest@mail.com>      ==============>  250 2.1.5 Recipient OK
    8. DATA                          ==============>  354 End data with <CR><LF>.<CR><LF>
    9. [Headers + MIME Body + .]     ==============>  250 2.0.0 OK: Message queued
    10. QUIT                         ==============>  221 2.0.0 Service closing channel
    """
    print(lifecycle_diagram)


# ==============================================================================
# SECTION 2: Modern EmailMessage vs Legacy MIMEText
# ==============================================================================
def create_modern_email(sender: str, recipient: str, subject: str, body: str) -> EmailMessage:
    """
    Constructs an email message using the modern Python 3.6+ EmailMessage API.
    
    Advantages of modern EmailMessage:
    - Automatically handles UTF-8 encoding and header folding according to RFC 5322.
    - Uniform API for plain text, HTML, and attachments without nested MIME multipart boilerplate.
    - Native support for internationalized domain names and emojis.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg["X-Mailer"] = "Python-Mastery-EmailMessage-v17"
    msg.set_content(body)
    return msg


def create_legacy_mimetext(sender: str, recipient: str, subject: str, body: str) -> MIMEText:
    """
    Constructs an email message using the legacy email.mime.text.MIMEText API.
    Retained for maintaining legacy codebases prior to Python 3.6.
    """
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    return msg


def demonstrate_message_formats() -> None:
    """Demonstrates differences between modern and legacy email construction."""
    print_banner("2. Modern EmailMessage API vs Legacy MIMEText")
    
    sender = "dev@automation.local"
    receiver = "client@company.org"
    subject = "🚀 Automated System Briefing [UTF-8 Support]"
    body = "Hello Team,\n\nThis is a plain-text notification dispatched by Python smtplib."

    modern_msg = create_modern_email(sender, receiver, subject, body)
    legacy_msg = create_legacy_mimetext(sender, receiver, subject, body)

    print("--- Modern EmailMessage Output (RFC 5322) ---")
    print(modern_msg.as_string()[:280] + "\n...")

    print("\n--- Legacy MIMEText Output ---")
    print(legacy_msg.as_string()[:280] + "\n...")


# ==============================================================================
# SECTION 3: Safe Credential Management & Configuration
# ==============================================================================
class EmailConfig:
    """
    Encapsulates SMTP configuration loaded safely from environment variables.
    Never hardcode passwords or API tokens directly into Python source files.
    """
    def __init__(self):
        self.smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.use_tls: bool = os.getenv("USE_TLS", "true").lower() in ("true", "1", "yes")
        self.use_ssl: bool = os.getenv("USE_SSL", "false").lower() in ("true", "1", "yes")
        self.username: Optional[str] = os.getenv("EMAIL_USER")
        self.password: Optional[str] = os.getenv("EMAIL_PASSWORD")
        self.simulation_mode: bool = os.getenv("SIMULATION_MODE", "true").lower() in ("true", "1", "yes")

    def is_configured_for_live(self) -> bool:
        """Checks if valid credentials have been set for live transmission."""
        return bool(self.username and self.password and not self.simulation_mode)

    def summary(self) -> Dict[str, Any]:
        return {
            "Server": self.smtp_server,
            "Port": self.smtp_port,
            "TLS (STARTTLS)": self.use_tls,
            "SSL": self.use_ssl,
            "User": self.username or "NOT_CONFIGURED (Using Simulation)",
            "Simulation Mode": self.simulation_mode or not self.is_configured_for_live(),
        }


# ==============================================================================
# SECTION 4: Dual-Engine Dispatcher (Simulation & Live STARTTLS/SSL)
# ==============================================================================
class SMTPDispatcher:
    """
    Production-grade SMTP dispatcher featuring:
    - Automatic fallback to Simulation Mode when credentials are not detected.
    - Explicit TLS context creation with secure ciphers (ssl.create_default_context).
    - Granular exception handling for network and authentication errors.
    """
    def __init__(self, config: EmailConfig):
        self.config = config

    def send_plain_text(
        self,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        debug_level: int = 0
    ) -> bool:
        """Dispatches a plain text email message."""
        msg = create_modern_email(sender, recipient, subject, body)

        if not self.config.is_configured_for_live():
            # Safe Simulation Mode for testing & learning without spamming
            self._simulate_transmission(msg)
            return True

        # Live SMTP Delivery
        try:
            print(f"[SMTP] Initiating TCP connection to {self.config.smtp_server}:{self.config.smtp_port}...")
            
            # Case 1: Implicit SSL (Port 465)
            if self.config.use_ssl:
                ssl_context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    context=ssl_context,
                    timeout=15
                ) as server:
                    if debug_level > 0:
                        server.set_debuglevel(debug_level)
                    server.login(self.config.username, self.config.password)
                    server.send_message(msg)
                    print(f"[SMTP Success] Email sent via SSL to {recipient}!")
                    return True

            # Case 2: Explicit STARTTLS (Port 587 - Recommended for Gmail / Outlook)
            else:
                with smtplib.SMTP(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=15
                ) as server:
                    if debug_level > 0:
                        server.set_debuglevel(debug_level)
                    
                    server.ehlo()  # Identify to the server
                    if self.config.use_tls:
                        ssl_context = ssl.create_default_context()
                        server.starttls(context=ssl_context)  # Upgrade to secure TLS channel
                        server.ehlo()  # Re-identify over encrypted channel
                    
                    if self.config.username and self.config.password:
                        server.login(self.config.username, self.config.password)
                    
                    server.send_message(msg)
                    print(f"[SMTP Success] Email sent via STARTTLS to {recipient}!")
                    return True

        except smtplib.SMTPAuthenticationError as auth_err:
            print(f"[SMTP Auth Error] Authentication failed: {auth_err}")
            print("Tip: If using Gmail, ensure 2-Factor Authentication is ON and use a 16-character App Password.")
            return False
        except smtplib.SMTPRecipientsRefused as rcpt_err:
            print(f"[SMTP Recipient Refused] Server rejected recipient: {rcpt_err}")
            return False
        except smtplib.SMTPServerDisconnected:
            print("[SMTP Disconnect Error] Server abruptly disconnected before completion.")
            return False
        except socket.timeout:
            print("[SMTP Timeout] Connection timed out while awaiting server response.")
            return False
        except Exception as general_err:
            print(f"[SMTP Unexpected Error] Failed to send email: {general_err}")
            return False

    def _simulate_transmission(self, msg: EmailMessage) -> None:
        """Simulates network dispatch and validates email structure."""
        print(f"\n[SIMULATION MODE ACTIVE] (Safe offline execution)")
        print(f"Connecting to Simulated Server : {self.config.smtp_server}:{self.config.smtp_port}")
        print(f">> EHLO client.domain")
        print(f">> STARTTLS (TLS v1.3 Verified)")
        print(f">> AUTH LOGIN: [User: {self.config.username or 'demo_user@domain.com'}] OK (235)")
        print(f">> MAIL FROM: <{msg['From']}> (250 OK)")
        print(f">> RCPT TO:   <{msg['To']}> (250 OK)")
        print(f">> DATA (Payload size: {len(msg.as_bytes())} bytes)")
        print(f">> Subject: \"{msg['Subject']}\"")
        print(f">> Message Dispatched Successfully! (250 2.0.0 Message Accepted)")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    print_banner("Day 17 - Module 1: SMTP Fundamentals & Plain Text Dispatch")
    
    # Step 1: Explain the protocol
    explain_smtp_lifecycle()

    # Step 2: Compare modern vs legacy message objects
    demonstrate_message_formats()

    # Step 3: Load configuration
    print_banner("3. SMTP Configuration Status")
    config = EmailConfig()
    for key, val in config.summary().items():
        print(f"  - {key:<20}: {val}")

    # Step 4: Dispatch a demonstration plain-text email
    print_banner("4. Plain-Text Automated Dispatch Demo")
    dispatcher = SMTPDispatcher(config)

    sender_email = config.username or "devops@cloudservice.io"
    recipient_email = os.getenv("DEFAULT_RECIPIENT", "developer@client.com")

    subject_line = "[AUTOMATION] Server Status Notification - Healthy"
    body_text = (
        "Hello Operations Lead,\n\n"
        "All scheduled background cron tasks and worker queues completed successfully.\n"
        "Total processed jobs: 4,821\n"
        "Failed jobs: 0\n"
        "System uptime: 99.98%\n\n"
        "--\nPython Email Automation Pipeline (Day 17)"
    )

    success = dispatcher.send_plain_text(
        sender=sender_email,
        recipient=recipient_email,
        subject=subject_line,
        body=body_text
    )

    print(f"\nDispatch result: {'SUCCESS' if success else 'FAILED'}")
