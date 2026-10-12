# Day 17: Python Email Automation & Processing Pipelines 📧

Welcome to **Day 17** of the Python Mastery Series! This repository provides an end-to-end, production-grade masterclass in **Python Email Automation**, covering the complete lifecycle of programmatically dispatching, formatting, templating, reading, and parsing emails using the standard Python library (`smtplib`, `email`, `imaplib`, `ssl`).

---

## 📁 Repository Structure

```text
DAY17-PYTHON/
│
├── 01_smtp_fundamentals_and_plain_text.py      # SMTP protocol handshake, STARTTLS vs SSL, modern EmailMessage, error handling
├── 02_html_emails_inline_assets_and_attachments.py # MIME hierarchy, responsive HTML, CID inline images, binary attachments, CC/BCC
├── 03_bulk_emailing_and_dynamic_templating.py  # string.Template personalization, CSV ingestion, connection reuse, rate limiting
├── 04_reading_parsing_and_imap_automation.py   # IMAP SSL (993), search queries, RFC 822 decoding, automated attachment harvester
├── 05_practical_projects.py                    # 4 Production mini-applications (Alert engine, Invoicing, Watchdog, Newsletter)
│
├── templates/                                  # Responsive, email-client compliant HTML templates
│   ├── welcome_email.html                      # Personalized member onboarding template with CTA button
│   ├── alert_notification.html                 # Infrastructure health alert with color-coded status badges
│   └── invoice_receipt.html                    # Itemized billing receipt table with automatic totals & tax
│
├── data/                                       # Sample datasets and attachments for testing
│   ├── subscribers.csv                         # Multi-column subscriber dataset (Name, Email, Plan, Date, Country)
│   ├── invoices.json                           # Customer billing data with itemized product catalogs
│   ├── sample_report.csv                       # Telemetry data artifact for attachment demonstrations
│   └── sample_logo.png                         # High-resolution PNG image for Content-ID (CID) inline embedding
│
├── .env.example                                # Configuration guide for Gmail, Outlook, Yahoo, and custom SMTP/IMAP
├── .gitignore                                  # Standard exclusions for logs, virtualenvs, credentials, and attachments
└── README.md                                   # Comprehensive masterclass documentation & execution guide
```

---

## 🧭 Architectural Overview

### 1. SMTP Handshake Lifecycle (Outbound Dispatch)
```text
CLIENT (Python smtplib)                          SMTP SERVER (e.g. Gmail / Postfix)
-----------------------                          ----------------------------------
1. Connect TCP (Port 587)        ==============>  220 smtp.gmail.com ESMTP ready
2. EHLO client.local             ==============>  250-STARTTLS (supported extension)
3. STARTTLS                      ==============>  220 Ready to start TLS
   [Secure TLS 1.3 handshake & CA certificate verification]
4. EHLO client.local (Encrypted) ===============>  250-AUTH LOGIN PLAIN
5. AUTH LOGIN (Base64 User/Pass) ===============>  235 Authentication successful
6. MAIL FROM: <sender@mail.com>  ==============>  250 Sender OK
7. RCPT TO: <dest@mail.com>      ==============>  250 Recipient OK
8. DATA                          ==============>  354 End data with <CR><LF>.<CR><LF>
9. [Headers + MIME Body + .]     ==============>  250 OK: Message queued
10. QUIT                         ==============>  221 Service closing channel
```

### 2. Nested MIME Multipart Hierarchy
```text
multipart/mixed  (Root container for the entire message payload)
|
+-- multipart/alternative  (Dual-payload engine: client chooses best format)
|   |
|   +-- text/plain  (Fallback for terminal clients, smartwatches, screen readers)
|   |
|   \-- multipart/related  (Rich media bundle)
|       |
|       +-- text/html  (HTML markup referencing <img src="cid:brand_logo">)
|       \-- image/png  (Inline embedded asset with Content-ID: <brand_logo>)
|
+-- application/pdf  (Attachment 1: Financial_Statement.pdf)
\-- text/csv         (Attachment 2: Telemetry_Export.csv)
```

---

## 📚 Masterclass Breakdown

### 1. SMTP Fundamentals & Plain Text (`01_smtp_fundamentals_and_plain_text.py`)
- **Modern `email.message.EmailMessage` API**: Replaces legacy `MIMEText` boilerplate with native UTF-8 support, automatic header folding according to RFC 5322, and seamless emoji support.
- **Security Protocols & Port Matrix**:
  - **Port 587 (STARTTLS)**: Opportunistic TLS upgrade. Modern standard recommended for Gmail, Outlook, and SendGrid.
  - **Port 465 (SMTPS)**: Implicit SSL from the initial TCP socket connection.
  - **Port 25**: Legacy unencrypted transmission (blocked by most residential ISPs and cloud providers).
- **Secure Credential Storage**: Loading credentials from `.env` and environment variables. Instructions on generating 16-character **Google App Passwords** with 2-Factor Authentication enabled.
- **Granular Exception Handling**:
  - `smtplib.SMTPAuthenticationError`: Invalid username, password, or missing App Password.
  - `smtplib.SMTPRecipientsRefused`: Server rejected recipient email address.
  - `smtplib.SMTPServerDisconnected`: Server closed socket before transaction finished.
  - `socket.timeout`: Network latency or firewall blocked port.
- **Dual Engine Execution**: Automatically runs in **Simulation Mode** if environment variables are not set, printing complete SMTP transactions without errors.

---

### 2. HTML Emails, Inline CID Images & Attachments (`02_html_emails_inline_assets_and_attachments.py`)
- **Dual-Payload Construction**: Pairing plain-text fallbacks with rich HTML markup so non-HTML readers can still read the message.
- **Inline CID Images**: Uses `Content-ID: <brand_logo>` headers so images render directly within HTML `<img src="cid:brand_logo">` tags without requiring external image hosting or triggering client blocking warnings.
- **Dynamic File Attachments**: Automatic MIME type and subtype detection using `mimetypes.guess_type()`, supporting PDFs, CSVs, PNGs, and ZIP archives.
- **Header Privacy & RFC 5322 Envelope Rules**:
  - `To` and `Cc`: Exposed in message headers and included in transport envelope.
  - `Bcc`: Included in SMTP transport recipient envelope (`RCPT TO`), but **omitted** from message headers to preserve recipient privacy.
- **MIME Tree Inspector**: Uses `message.walk()` to display a visual diagnostic table of all parts, content types, byte sizes, and dispositions.

---

### 3. Bulk Emailing & Dynamic HTML Templating (`03_bulk_emailing_and_dynamic_templating.py`)
- **Dynamic Personalization**: Employs Python's standard `string.Template` for safe variable substitution (`${user_name}`, `${plan_tier}`) without external dependencies like Jinja2.
- **CSV Subscriber Ingestion**: Parses recipient datasets with `csv.DictReader` and validates email addresses against standard RFC regex rules.
- **Connection Reuse / Session Pooling**: Reuses a single authenticated SMTP connection across an entire batch of recipients, avoiding repeated TCP and TLS overhead.
- **Adaptive Throttling**: Configurable delay between transmissions (`DISPATCH_DELAY_SECONDS`) to maintain IP reputation and adhere to provider rate limits.
- **Anti-Spam & Deliverability Standards**:
  - Adds RFC-compliant `List-Unsubscribe` headers (`<mailto:...>`, `<https://...>`).
  - Generates unique cryptographic `Message-ID` per email using `email.utils.make_msgid()`.
  - Formats friendly recipient headers: `Recipient Name <recipient@example.com>` using `email.utils.formataddr()`.
- **Audit Logging**: Exports a complete JSON dispatch telemetry report (`dispatch_audit_report.json`).

---

### 4. Reading Emails & IMAP Automation (`04_reading_parsing_and_imap_automation.py`)
- **Protocol Matrix (IMAP vs POP3 vs SMTP)**:
  - **SMTP**: Outbound delivery (push).
  - **IMAP (Port 993 SSL)**: Two-way synchronization. Folders and flags (`\Seen`, `\Flagged`, `\Deleted`) stay synchronized on server.
  - **POP3 (Port 995 SSL)**: One-way single-client download and delete.
- **Mailbox Operations**:
  - Secure connection with `imaplib.IMAP4_SSL`.
  - Selecting mailboxes in Read-Only (`readonly=True`) or Read-Write mode.
  - Search criteria: `ALL`, `UNSEEN`, `FROM "support@domain.com"`, `SUBJECT "Invoice"`, date range filtering.
- **Payload Decoding & Harvesting**:
  - Decodes multilingual RFC 2047 encoded subject headers using `email.header.decode_header`.
  - Parses raw RFC 822 byte streams into `email.message.EmailMessage` with `email.message_from_bytes()`.
  - Automatically identifies attachments, sanitizes filenames to prevent path traversal attacks, and saves them to local storage.
  - Computes cryptographic **SHA-256 hashes** for attachment deduplication and data integrity.

---

### 5. Production Projects (`05_practical_projects.py`)

| Project | Description | Key Modules / Concepts |
| :--- | :--- | :--- |
| **1. Server Health Alert Monitor** | Gathers system telemetry (CPU, RAM, Disk), evaluates threshold breaches, compiles color-coded HTML alerts with severity badges, attaches diagnostic dumps, and notifies SRE on-call engineers. | `socket`, `datetime`, `string.Template`, `EmailMessage`, Priority Headers (`X-Priority: 1`). |
| **2. Invoice & Statement Dispatcher** | Ingests JSON customer orders, calculates subtotals, tax rates, and final amounts, renders responsive itemized HTML receipts, attaches dynamic CSV statements, and dispatches to billing contacts. | `json`, `csv`, `string.Template`, Currency formatting, Dynamic HTML table generation. |
| **3. Inbox Watchdog & Invoice Harvester** | Scans mailbox for incoming vendor bills, verifies attachments, computes SHA-256 hashes to prevent duplicate file storage, partitions files into `YYYY-MM` directories, and replies with automated confirmation receipts. | `hashlib`, `os.path`, Date partitioning, Duplicate detection, Auto-acknowledgment emails. |
| **4. Executive Digest & Newsletter Engine** | Compiles daily business KPIs (MRR, active users, uptime), personalizes HTML digest emails across subscribers, enforces dispatch rate-limiting, and logs campaign speed metrics. | `csv.DictReader`, `time.sleep`, Rate limiting, Campaign metrics, Deliverability. |

---

## 🚀 Quickstart & Execution Guide

### Prerequisites
- Python 3.8+ installed (tested on Python 3.11+).
- All scripts use the Python Standard Library. **No `pip install` required!**

### Step 1: Clone or Navigate to the Repository
```bash
git clone https://github.com/sameer481/DAY17-PYTHON.git
cd DAY17-PYTHON
```

### Step 2: Run in Simulation Mode (Zero Configuration)
All scripts run out-of-the-box in **Simulation Mode** without needing real email credentials or internet access:

```bash
# 1. Run SMTP Fundamentals & Plain Text Demo
python 01_smtp_fundamentals_and_plain_text.py

# 2. Run HTML, Inline Images & Attachments Demo
python 02_html_emails_inline_assets_and_attachments.py

# 3. Run Bulk Dispatch & Dynamic Templating Demo
python 03_bulk_emailing_and_dynamic_templating.py

# 4. Run IMAP Email Reading & Attachment Harvester Demo
python 04_reading_parsing_and_imap_automation.py

# 5. Run all 4 Production Projects
python 05_practical_projects.py
```

---

## 🔒 Live Mode Setup (Optional: Real Gmail / Outlook Dispatch)

To connect to real email servers:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. For **Gmail**:
   - Enable **2-Step Verification** in your Google Account (`Security` -> `2-Step Verification`).
   - Go to `App passwords` (search for "App passwords" in Google Account settings).
   - Generate an App Password for "Mail" (gives you a 16-character code like `abcd efgh ijkl mnop`).
   - Enter your email and the 16-character code into `.env`:
     ```env
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     USE_TLS=true
     EMAIL_USER=your_email@gmail.com
     EMAIL_PASSWORD=your_16_char_app_password
     SIMULATION_MODE=false
     ```
3. Run any script to send real emails!

---

## 🛡️ Deliverability & Anti-Spam Best Practices

To ensure high inbox placement and prevent emails from landing in spam folders:
1. **Always provide a plain-text alternative**: Spam filters score emails lacking a plain-text body negatively.
2. **Include List-Unsubscribe headers**: Required for bulk mailings under Google and Yahoo sender guidelines (2024+).
3. **Use friendly sender formatting**: Format headers as `Your Name <you@domain.com>` rather than raw addresses.
4. **Implement rate limiting / throttling**: Never send hundreds of emails per second from a single IP without warming up.
5. **Verify domain DNS records**: Ensure your sending domain has valid **SPF** (Sender Policy Framework), **DKIM** (DomainKeys Identified Mail), and **DMARC** (Domain-based Message Authentication) records configured.

---

## 📝 License & Contributing

Created as part of the **Python Mastery Series** by [Sameer Mohammed](https://github.com/sameer481). Open-sourced for educational and professional software development. Contributions and suggestions via pull requests are always welcome!
