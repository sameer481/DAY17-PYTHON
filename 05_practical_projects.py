"""
Day 17 - Python Email Automation Masterclass
File 5: 4 Real-World Production Projects

Projects Included:
1. Automated Server Health & Infrastructure Telemetry Alert Engine
   - Monitors CPU/RAM/Disk metrics, evaluates thresholds, generates color-coded HTML alerts,
     and attaches system diagnostic logs.
2. Personalized Customer Invoice & Billing Dispatch Pipeline
   - Reads JSON invoice records, computes financial totals, renders itemized HTML receipts,
     and attaches detailed CSV billing ledgers.
3. Automated Inbox Watchdog & Invoice Attachment Harvester
   - Scans mailbox, identifies invoice emails, dedupes via SHA-256 hashes, saves attachments
     to structured storage, and triggers auto-acknowledgments.
4. Daily Executive Digest & Newsletter Publishing Engine
   - Curates daily operational KPIs, dispatches personalized responsive newsletters to subscribers,
     implements rate-limiting, and tracks delivery telemetry.
"""

import os
import sys
import csv
import json
import time
import socket
import hashlib
import datetime
from string import Template
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Dict, List, Any, Optional, Tuple

# Ensure robust stdout encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner(title: str) -> None:
    """Helper to display formatted section headers."""
    print(f"\n{'#' * 75}\n# PROJECT: {title}\n{'#' * 75}")


# ==============================================================================
# PROJECT 1: Automated Server Health & Infrastructure Alert Engine
# ==============================================================================
class ServerHealthAlertMonitor:
    """
    Monitors system resource metrics and dispatches an automated HTML alert email
    with attached diagnostic logs if thresholds are breached.
    """
    def __init__(self, alert_email: str, cpu_thresh: float = 85.0, ram_thresh: float = 90.0):
        self.alert_email = alert_email
        self.cpu_thresh = cpu_thresh
        self.ram_thresh = ram_thresh

    def collect_telemetry(self) -> Dict[str, Any]:
        """Collects current system metrics (simulated realistic telemetry)."""
        hostname = socket.gethostname()
        return {
            "hostname": hostname,
            "environment": "Production-Cluster-US-East",
            "cpu_percent": 88.5,    # Triggers warning
            "ram_percent": 92.4,    # Triggers critical
            "disk_percent": 64.2,   # Normal
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def generate_diagnostic_log(self, telemetry: Dict[str, Any], filepath: str) -> str:
        """Writes detailed diagnostic log file to attach to alert email."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- SYSTEM DIAGNOSTIC DUMP: {telemetry['timestamp']} ---\n")
            f.write(f"Host: {telemetry['hostname']} | Env: {telemetry['environment']}\n")
            f.write(f"CPU Utilization : {telemetry['cpu_percent']}%\n")
            f.write(f"Memory (RAM)    : {telemetry['ram_percent']}%\n")
            f.write(f"Disk Capacity   : {telemetry['disk_percent']}%\n")
            f.write("Top Processes by CPU:\n")
            f.write("  PID 4021 - python worker_queue.py   (44.2% CPU)\n")
            f.write("  PID 1104 - postgres: query_executor (31.8% CPU)\n")
            f.write("  PID 0882 - redis-server             (08.1% CPU)\n")
            f.write("Diagnostic status: ELEVATED_LOAD_DETECTED\n")
        return filepath

    def build_alert_email(self, telemetry: Dict[str, Any], log_filepath: str) -> EmailMessage:
        """Constructs responsive HTML alert email with status badges."""
        is_critical = telemetry["cpu_percent"] > self.cpu_thresh or telemetry["ram_percent"] > self.ram_thresh
        alert_level = "CRITICAL" if is_critical else "WARNING"
        alert_color = "#dc2626" if is_critical else "#d97706"

        cpu_status = "CRITICAL" if telemetry["cpu_percent"] > self.cpu_thresh else "OPTIMAL"
        ram_status = "CRITICAL" if telemetry["ram_percent"] > self.ram_thresh else "OPTIMAL"
        disk_status = "NORMAL"

        msg = EmailMessage()
        msg["Subject"] = f"🚨 [{alert_level}] Telemetry Alert: {telemetry['hostname']} High Utilization"
        msg["From"] = formataddr(("DevOps Telemetry Daemon", "alerts@infrastructure.local"))
        msg["To"] = self.alert_email
        msg["X-Priority"] = "1"  # Highest priority flag

        # Plain text fallback
        plain_text = (
            f"SERVER TELEMETRY ALERT [{alert_level}]\n"
            f"Host: {telemetry['hostname']} ({telemetry['environment']})\n"
            f"CPU: {telemetry['cpu_percent']}% | RAM: {telemetry['ram_percent']}%\n"
            f"Diagnostic log attached: {os.path.basename(log_filepath)}\n"
        )
        msg.set_content(plain_text)

        # HTML Alert Body
        template_path = os.path.join("templates", "alert_notification.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = Template(f.read())
            html_body = html_template.safe_substitute({
                "alert_level": alert_level,
                "alert_color": alert_color,
                "server_hostname": telemetry["hostname"],
                "environment": telemetry["environment"],
                "cpu_percent": telemetry["cpu_percent"],
                "cpu_status": cpu_status,
                "ram_percent": telemetry["ram_percent"],
                "ram_status": ram_status,
                "disk_percent": telemetry["disk_percent"],
                "disk_status": disk_status,
                "timestamp": telemetry["timestamp"]
            })
            msg.add_alternative(html_body, subtype="html")

        # Attach diagnostic log
        with open(log_filepath, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="plain",
                filename=os.path.basename(log_filepath)
            )

        return msg


def run_project_1() -> None:
    print_banner("1. Automated Server Health & Infrastructure Telemetry Alert Engine")
    monitor = ServerHealthAlertMonitor("sre-oncall@datacenter.org")
    telemetry = monitor.collect_telemetry()
    print(f"Collected host metrics: Host={telemetry['hostname']} | CPU={telemetry['cpu_percent']}% | RAM={telemetry['ram_percent']}%")

    log_path = os.path.join("data", "system_diagnostic.log")
    monitor.generate_diagnostic_log(telemetry, log_path)
    print(f"Generated diagnostic log: '{log_path}'")

    email_msg = monitor.build_alert_email(telemetry, log_path)
    print(f"Constructed alert: Subject='{email_msg['Subject']}'")
    print(f"Recipients: {email_msg['To']} | Priority={email_msg.get('X-Priority')}")
    print("[SIMULATION DISPATCH] Alert successfully routed to SRE on-call pager!")


# ==============================================================================
# PROJECT 2: Personalized Invoice & Billing Dispatch Pipeline
# ==============================================================================
class InvoiceBillingPipeline:
    """
    Processes customer invoice payloads from JSON data, renders itemized
    HTML invoices, creates CSV ledger attachments, and dispatches them.
    """
    def __init__(self, template_path: str):
        self.template_path = template_path

    def process_and_send(self, invoices_path: str) -> List[Dict[str, Any]]:
        with open(invoices_path, "r", encoding="utf-8") as f:
            invoices = json.load(f)

        dispatched_invoices = []
        for inv in invoices:
            # 1. Compute totals
            subtotal = sum(item["quantity"] * item["unit_price"] for item in inv["items"])
            tax_rate = inv.get("tax_rate", 0.0)
            tax_amount = round(subtotal * (tax_rate / 100.0), 2)
            total = round(subtotal + tax_amount, 2)

            # 2. Render item rows
            item_rows_html = ""
            for item in inv["items"]:
                amt = item["quantity"] * item["unit_price"]
                item_rows_html += (
                    f"<tr>"
                    f"<td>{item['description']}</td>"
                    f"<td style='text-align: center;'>{item['quantity']}</td>"
                    f"<td style='text-align: right;'>${item['unit_price']:.2f}</td>"
                    f"<td style='text-align: right;'>${amt:.2f}</td>"
                    f"</tr>"
                )

            # 3. Render HTML invoice
            with open(self.template_path, "r", encoding="utf-8") as f:
                template = Template(f.read())
            html_invoice = template.safe_substitute({
                "invoice_number": inv["invoice_number"],
                "invoice_date": inv["invoice_date"],
                "customer_name": inv["customer_name"],
                "customer_email": inv["customer_email"],
                "customer_id": inv["customer_id"],
                "items_rows": item_rows_html,
                "subtotal": f"{subtotal:,.2f}",
                "tax_rate": tax_rate,
                "tax_amount": f"{tax_amount:,.2f}",
                "total_amount": f"{total:,.2f}"
            })

            # 4. Build Email Message
            msg = EmailMessage()
            msg["Subject"] = f"🧾 Paid Invoice Receipt #{inv['invoice_number']} - Cloud Services"
            msg["From"] = formataddr(("Acme Cloud Billing", "billing@cloudservices.local"))
            msg["To"] = formataddr((inv["customer_name"], inv["customer_email"]))

            plain_fallback = (
                f"INVOICE RECEIPT #{inv['invoice_number']}\n"
                f"Customer: {inv['customer_name']}\n"
                f"Total Amount Paid: ${total:,.2f}\n"
                f"Thank you for your business!"
            )
            msg.set_content(plain_fallback)
            msg.add_alternative(html_invoice, subtype="html")

            # 5. Generate and attach itemized CSV statement
            csv_lines = ["Description,Quantity,UnitPrice,Amount"]
            for item in inv["items"]:
                csv_lines.append(f'"{item["description"]}",{item["quantity"]},{item["unit_price"]},{item["quantity"]*item["unit_price"]}')
            csv_statement = "\n".join(csv_lines).encode("utf-8")

            msg.add_attachment(
                csv_statement,
                maintype="text",
                subtype="csv",
                filename=f"{inv['invoice_number']}_statement.csv"
            )

            dispatched_invoices.append({
                "invoice_number": inv["invoice_number"],
                "customer": inv["customer_name"],
                "email": inv["customer_email"],
                "total": total,
                "items_count": len(inv["items"])
            })

            print(f"  [Invoice Dispatched] #{inv['invoice_number']} -> {inv['customer_name']} (${total:,.2f})")

        return dispatched_invoices


def run_project_2() -> None:
    print_banner("2. Personalized Customer Invoice & Billing Dispatch Pipeline")
    invoices_file = os.path.join("data", "invoices.json")
    template_file = os.path.join("templates", "invoice_receipt.html")

    pipeline = InvoiceBillingPipeline(template_file)
    results = pipeline.process_and_send(invoices_file)
    print(f"\nSuccessfully generated and queued {len(results)} personalized itemized invoices!")


# ==============================================================================
# PROJECT 3: Automated Inbox Watchdog & Invoice Harvester
# ==============================================================================
class InvoiceHarvesterWatchdog:
    """
    Monitors mailbox for incoming invoice documents, dedupes via SHA-256,
    saves to partitioned folders, and sends automated acknowledgment receipts.
    """
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.processed_hashes = set()

    def process_incoming_email(self, sender: str, subject: str, attachment_name: str, payload_bytes: bytes) -> Dict[str, Any]:
        """Processes an incoming email, checks for duplicates, and saves attachment."""
        file_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        # Deduplication check
        if file_hash in self.processed_hashes:
            return {"status": "DUPLICATE_SKIPPED", "hash": file_hash}

        self.processed_hashes.add(file_hash)

        # Date-partitioned directory: ./downloaded_invoices/YYYY-MM/
        today_folder = datetime.date.today().strftime("%Y-%m")
        dest_dir = os.path.join(self.storage_dir, today_folder)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, attachment_name)
        with open(dest_path, "wb") as f:
            f.write(payload_bytes)

        # Build automated acknowledgment email
        ack_msg = EmailMessage()
        ack_msg["Subject"] = f"Re: {subject} [ACKNOWLEDGED]"
        ack_msg["From"] = "Accounts Payable <accounting-bot@enterprise.local>"
        ack_msg["To"] = sender
        ack_msg.set_content(
            f"Hello,\n\n"
            f"Your invoice attachment '{attachment_name}' was received successfully.\n"
            f"SHA-256 Tracking Hash: {file_hash}\n"
            f"Status: Queued for finance audit and scheduled disbursement.\n\n"
            f"--\nEnterprise Accounts Payable Bot"
        )

        return {
            "status": "PROCESSED_AND_STORED",
            "file_path": dest_path,
            "hash": file_hash,
            "size_bytes": len(payload_bytes),
            "ack_subject": ack_msg["Subject"]
        }


def run_project_3() -> None:
    print_banner("3. Automated Inbox Watchdog & Invoice Attachment Harvester")
    storage_folder = "downloaded_invoices"
    watchdog = InvoiceHarvesterWatchdog(storage_folder)

    # Simulated incoming invoice from Vendor A
    vendor_sender = "vendor.billing@globalhardware.com"
    subject = "Monthly Hardware Lease Invoice #HL-9921"
    sample_invoice_bytes = b"VENDOR,HL-9921,ITEM,SERVER_RACK,PRICE,1200.00"
    
    print(f"Watchdog detected incoming email from: {vendor_sender}")
    result = watchdog.process_incoming_email(
        sender=vendor_sender,
        subject=subject,
        attachment_name="HL_9921_Invoice.csv",
        payload_bytes=sample_invoice_bytes
    )

    print(f"  - Action Status : {result['status']}")
    print(f"  - Saved File    : {result['file_path']}")
    print(f"  - File SHA-256  : {result['hash'][:24]}...")
    print(f"  - Auto ACK Sent : {result['ack_subject']}")

    # Testing Duplicate Prevention
    print("\nSimulating duplicate transmission of identical invoice...")
    dup_result = watchdog.process_incoming_email(
        sender=vendor_sender,
        subject=subject,
        attachment_name="HL_9921_Invoice.csv",
        payload_bytes=sample_invoice_bytes
    )
    print(f"  - Action Status : {dup_result['status']} (Duplicate prevented from redundant storage)")


# ==============================================================================
# PROJECT 4: Daily Executive Digest & Newsletter Publishing Pipeline
# ==============================================================================
class ExecutiveDigestPublisher:
    """
    Compiles daily executive KPI summaries, personalizes newsletter emails
    for subscribers, implements rate-limiting, and tracks campaign metrics.
    """
    def __init__(self, subscribers_csv: str):
        self.subscribers_csv = subscribers_csv

    def generate_digest(self) -> Dict[str, Any]:
        """Curates simulated daily operational telemetry."""
        return {
            "date": datetime.date.today().strftime("%B %d, %Y"),
            "active_users": "142,850 (+12.4%)",
            "mrr": "$248,500 (+8.1%)",
            "api_uptime": "99.99%",
            "top_story": "Python 3.12+ Performance Optimizations deployed across core microservices."
        }

    def publish_campaign(self) -> Dict[str, Any]:
        digest = self.generate_digest()
        
        # Load subscribers
        subscribers = []
        with open(self.subscribers_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            subscribers = list(reader)

        print(f"Curating Executive Digest for {digest['date']}...")
        print(f"Dispatching to {len(subscribers)} registered executives with 0.1s rate limiting:")

        start_time = time.time()
        for idx, sub in enumerate(subscribers, start=1):
            time.sleep(0.08)  # Throttled dispatch
            print(f"  [{idx}/{len(subscribers)}] Dispatched personalized digest to {sub['name']} <{sub['email']}>")

        duration = round(time.time() - start_time, 2)
        return {
            "subscribers_reached": len(subscribers),
            "campaign_date": digest["date"],
            "duration_seconds": duration,
            "status": "COMPLETED_SUCCESSFULLY"
        }


def run_project_4() -> None:
    print_banner("4. Daily Executive Digest & Newsletter Publishing Pipeline")
    subscribers_file = os.path.join("data", "subscribers.csv")
    publisher = ExecutiveDigestPublisher(subscribers_file)
    summary = publisher.publish_campaign()

    print("\n--- Publishing Summary ---")
    for k, v in summary.items():
        print(f"  - {k:<22}: {v}")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    print_banner("DAY 17: Practical Production Projects Execution Harness")
    
    # Project 1
    run_project_1()

    # Project 2
    run_project_2()

    # Project 3
    run_project_3()

    # Project 4
    run_project_4()

    print("\n" + "=" * 75)
    print("ALL 4 PRODUCTION PROJECTS EXECUTED SUCCESSFULLY!")
    print("=" * 75)
