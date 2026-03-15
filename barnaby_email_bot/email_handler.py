"""
Email Handler for Unity MMA
IMAP/SMTP integration with intent classification
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import json
import os
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import (
    EMAIL_HOST, IMAP_PORT, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD,
    XAI_API_KEY, GYM_INFO, EMAIL_TEMPLATES, TIMETABLE_EMAIL,
    INTENT_CATEGORIES, EMAIL_ACCOUNTS
)

# Initialize AI model for intent classification
model = ChatXAI(model="grok-3", temperature=0.3, api_key=XAI_API_KEY) if XAI_API_KEY else None

# Email processing log
EMAIL_LOG_FILE = os.path.expanduser("~/junction-ai/barnaby_email_bot/email_log.json")

def load_email_log():
    try:
        with open(EMAIL_LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"processed": [], "escalations": [], "stats": {"total": 0, "auto_replied": 0, "escalated": 0, "ignored": 0}}

def save_email_log(log):
    os.makedirs(os.path.dirname(EMAIL_LOG_FILE), exist_ok=True)
    with open(EMAIL_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, default=str)


class EmailBot:
    """Unity MMA Email Bot with IMAP/SMTP integration."""

    def __init__(self, email_user: str = None, email_password: str = None, account_name: str = "default"):
        self.imap = None
        self.smtp = None
        self.log = load_email_log()
        # Support custom credentials for multi-inbox
        self.email_user = email_user or EMAIL_USER
        self.email_password = email_password or EMAIL_PASSWORD
        self.account_name = account_name

    def connect_imap(self) -> bool:
        """Connect to IMAP server for reading emails."""
        try:
            self.imap = imaplib.IMAP4_SSL(EMAIL_HOST, IMAP_PORT)
            self.imap.login(self.email_user, self.email_password)
            return True
        except Exception as e:
            print(f"[{self.account_name}] IMAP connection error: {e}")
            return False

    def connect_smtp(self) -> bool:
        """Connect to SMTP server for sending emails.
        Uses primary account (info@) for auth - FreeParking allows sending FROM any domain address.
        """
        try:
            self.smtp = smtplib.SMTP_SSL(EMAIL_HOST, SMTP_PORT)
            # Always auth with primary account (info@) - FreeParking SMTP restriction
            self.smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            print(f"[{self.account_name}] SMTP authenticated as {EMAIL_USER} (will send FROM {self.email_user})")
            return True
        except Exception as e:
            print(f"[{self.account_name}] SMTP connection error: {e}")
            return False

    def disconnect(self):
        """Close email connections."""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                pass

    def fetch_unread_emails(self, folder: str = "INBOX", limit: int = 10) -> List[Dict]:
        """Fetch unread emails from inbox."""
        # Always reconnect for fresh state
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
            self.imap = None

        if not self.connect_imap():
            print(f"[{self.account_name}] [IMAP ERROR] Failed to connect")
            return []

        emails = []
        try:
            # Select folder (use read-write mode to allow marking as seen)
            status, _ = self.imap.select(folder)
            if status != 'OK':
                print(f"[IMAP] Failed to select folder: {folder}")
                return []

            # Search for UNSEEN emails
            status, message_numbers = self.imap.search(None, "UNSEEN")
            if status != 'OK':
                print(f"[IMAP] Search failed")
                return []

            msg_nums = message_numbers[0].split()
            print(f"[{self.account_name}] Found {len(msg_nums)} unread email(s) in {folder}")

            for num in msg_nums[:limit]:
                try:
                    # Fetch email (BODY.PEEK to not auto-mark as read yet)
                    _, msg_data = self.imap.fetch(num, "(BODY.PEEK[])")
                    if msg_data[0] is None:
                        continue

                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    # Parse email
                    parsed = self._parse_email(msg)
                    parsed["message_id"] = num.decode()
                    parsed["_imap_num"] = num  # Store for marking as read later
                    parsed["inbox"] = self.account_name  # Track which inbox
                    emails.append(parsed)
                    print(f"[{self.account_name}] Fetched: {parsed['subject'][:50]}...")
                except Exception as e:
                    print(f"[IMAP] Error fetching message {num}: {e}")

        except Exception as e:
            print(f"[IMAP ERROR] {type(e).__name__}: {e}")

        return emails

    def mark_as_read(self, email_data: Dict) -> bool:
        """Mark an email as read (SEEN) in IMAP."""
        imap_num = email_data.get("_imap_num")
        if not imap_num:
            return False

        try:
            if not self.imap:
                self.connect_imap()
                self.imap.select("INBOX")

            self.imap.store(imap_num, '+FLAGS', '\\Seen')
            print(f"[IMAP] Marked as read: {email_data.get('subject', 'unknown')[:30]}...")
            return True
        except Exception as e:
            print(f"[IMAP] Failed to mark as read: {e}")
            return False

    def _parse_email(self, msg) -> Dict:
        """Parse email message into structured dict."""
        # Decode subject
        subject = ""
        if msg["Subject"]:
            decoded = decode_header(msg["Subject"])
            subject = decoded[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(decoded[0][1] or "utf-8")

        # Get sender
        sender = msg.get("From", "")
        sender_name = ""
        sender_email = sender

        # Extract name from "Name <email>" format
        match = re.match(r'"?([^"<]+)"?\s*<([^>]+)>', sender)
        if match:
            sender_name = match.group(1).strip()
            sender_email = match.group(2).strip()

        # Get body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

        return {
            "subject": subject,
            "sender": sender,
            "sender_name": sender_name or sender_email.split("@")[0].title(),
            "sender_email": sender_email,
            "body": body[:2000],  # Limit body length
            "date": msg.get("Date", ""),
            "timestamp": datetime.now().isoformat()
        }

    def classify_intent(self, email_data: Dict) -> Tuple[str, str, float]:
        """
        Classify email intent using AI.
        Returns: (intent, action, confidence)
        """
        if not model:
            return self._rule_based_classify(email_data)

        system_prompt = """You are an email classifier for Unity MMA gym. Barnaby (owner) wants PERSONAL questions escalated for human reply.

ESCALATE (check FIRST - needs human touch):
1. CANCELLATION/BILLING: cancel, stop, pause, freeze, payment, refund, billing, charge
2. PERSONAL QUESTIONS (CRITICAL - these need coach advice):
   - Experience level mentioned: "been training", "few months", "few weeks", "experience"
   - Permission questions: "is it ok if", "can I come", "am I ready", "suitable for"
   - Concerns: "nervous", "anxious", "worried", "scared", "intimidated"
   - Health/injury: "injury", "injured", "knee", "back", "shoulder", "condition"
   - Skill questions: "level", "skill level", "ability", "ready for sparring"
   - Sparring/competition: "sparring", "spar", "compete", "competition", "fight"
   - Advice seeking: "advice", "recommend", "which class", "best for me"
3. COMPLAINTS: unhappy, disappointed, frustrated, problem
4. PT ENQUIRY: personal training, private session, 1-on-1

AUTO-REPLY (ONLY for simple, generic questions with NO personal context):
- first_timer: Pure "interested in joining" with no specific questions
- class_info: Simple "what classes?" or "what times?" (NO experience/level mentioned)
- promo_clarification: Simple "how much?" pricing question
- location_info: "where are you located?"

IGNORE: noreply, automated, receipt, invoice, unsubscribe

RULE: If the email mentions ANY personal situation, experience level, health concern, or asks for advice → ESCALATE as personal_question

Respond with ONLY JSON: {"intent": "intent_name", "action": "auto_reply|escalate|ignore", "confidence": 0.0-1.0}
"""

        user_message = f"""
Subject: {email_data['subject']}
From: {email_data['sender']}
Body: {email_data['body'][:500]}
"""

        try:
            response = model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])

            # Parse JSON response
            content = response.content.strip()
            # Extract JSON if wrapped in markdown
            if "```" in content:
                content = re.search(r'\{[^}]+\}', content).group()

            result = json.loads(content)
            return (
                result.get("intent", "unknown"),
                result.get("action", "escalate"),
                result.get("confidence", 0.5)
            )
        except Exception as e:
            print(f"AI classification error: {e}")
            return self._rule_based_classify(email_data)

    def _rule_based_classify(self, email_data: Dict) -> Tuple[str, str, float]:
        """Fallback rule-based classification."""
        subject = email_data["subject"].lower()
        body = email_data["body"].lower()

        # CRITICAL: Check SUBJECT LINE FIRST for cancel keywords
        # If subject contains cancel/stop → ESCALATE immediately, don't even read body
        subject_cancel_keywords = ["cancel", "cancellation", "stop", "terminate", "quit", "ending"]
        if any(w in subject for w in subject_cancel_keywords):
            return ("cancellation", "escalate", 0.99)

        combined = f"{subject} {body}"

        # Check for ignore patterns
        ignore_patterns = ["unsubscribe", "noreply", "no-reply", "automated", "receipt", "invoice"]
        if any(p in combined for p in ignore_patterns):
            return ("system_noise", "ignore", 0.8)

        # PRIORITY: Check for escalation patterns FIRST (before auto-reply)
        # Cancel/membership termination - ALWAYS escalate - expanded keywords
        cancel_keywords = ["cancel", "cancellation", "end my membership", "stop membership",
                          "terminate", "quit", "leaving", "not renewing", "don't want to continue",
                          "pause", "break", "ending", "done with", "finish my", "close my account"]
        if any(w in combined for w in cancel_keywords):
            return ("cancellation", "escalate", 0.99)

        # Billing/payment issues - ALWAYS escalate
        billing_keywords = ["payment failed", "billing", "charge", "refund", "overcharged",
                           "double charged", "card declined", "payment issue", "money back"]
        if any(w in combined for w in billing_keywords):
            return ("billing_issue", "escalate", 0.9)

        # Personal training requests - escalate for coach follow-up
        if any(w in combined for w in ["personal training", "pt session", "one on one", "1 on 1", "private session"]):
            return ("pt_enquiry", "escalate", 0.8)

        # Complaints - ALWAYS escalate
        if any(w in combined for w in ["complaint", "unhappy", "disappointed", "problem", "issue", "frustrated"]):
            return ("complaint", "escalate", 0.9)

        # PERSONAL/NUANCED questions - need human touch, escalate for coach advice
        # These indicate experience level, specific situations, or personal concerns
        personal_keywords = [
            "been training", "few months", "few weeks", "been doing", "experience",
            "is it ok if", "ok if i", "can i come", "am i ready", "ready for",
            "suitable for", "right for me", "good for", "appropriate",
            "nervous", "anxious", "worried", "scared", "intimidated",
            "injury", "injured", "knee", "back", "shoulder", "condition", "health",
            "level", "skill level", "ability", "fitness level",
            "sparring", "spar", "compete", "competition", "fight",
            "advice", "recommend", "suggestion", "which class", "best for"
        ]
        if any(w in combined for w in personal_keywords):
            return ("personal_question", "escalate", 0.9)

        # Check for auto-reply patterns (only GENERIC questions - no personal context)
        if any(w in combined for w in ["interested", "join", "start", "try", "new member", "first time"]):
            return ("first_timer", "auto_reply", 0.8)
        if any(w in combined for w in ["class", "schedule", "timetable", "when is", "what time"]):
            return ("class_info", "auto_reply", 0.8)
        if any(w in combined for w in ["price", "cost", "trial", "free"]):
            return ("promo_clarification", "auto_reply", 0.8)
        if any(w in combined for w in ["where", "location", "address", "directions"]):
            return ("location_info", "auto_reply", 0.8)
        if any(w in combined for w in ["confirm", "booked", "thank"]):
            return ("booking_confirm", "auto_reply", 0.7)

        # Default to escalate if unsure
        return ("unknown", "escalate", 0.5)

    def generate_response(self, email_data: Dict, intent: str) -> str:
        """Generate email response based on intent."""
        template = EMAIL_TEMPLATES.get(intent, "")

        if not template:
            return ""

        # Prepare template variables
        name = email_data.get("sender_name", "there")

        # Get class info if needed
        class_info = TIMETABLE_EMAIL if intent == "class_info" else ""

        # Format response
        response = template.format(
            name=name,
            phone=GYM_INFO["phone"],
            email=GYM_INFO["email"],
            location=GYM_INFO["location"],
            trial_url=GYM_INFO["trial_url"],
            booking_url=GYM_INFO["booking_url"],
            class_info=class_info
        )

        return response

    def send_email(self, to: str, subject: str, body: str, reply_to_subject: str = None) -> bool:
        """Send email via SMTP with detailed error handling.
        Auth as primary (info@), send FROM receiving inbox address.
        Saves sent email to Sent folder via IMAP APPEND.
        """
        print(f"[{self.account_name}] [SMTP] Attempting to send email to: {to}")
        print(f"[{self.account_name}] [SMTP] Will send FROM: {self.email_user} (auth as {EMAIL_USER})")

        # Always reconnect for reliability
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                pass
            self.smtp = None

        if not self.connect_smtp():
            print(f"[{self.account_name}] [SMTP ERROR] Failed to connect to SMTP server")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = f"Unity MMA <{self.email_user}>"
            msg["To"] = to
            msg["Reply-To"] = self.email_user  # Ensure replies go to same inbox
            msg["Subject"] = f"Re: {reply_to_subject}" if reply_to_subject else subject
            msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +1300")  # NZ timezone

            msg.attach(MIMEText(body, "plain"))

            print(f"[{self.account_name}] [SMTP] Sending from {self.email_user} to {to}...")
            self.smtp.send_message(msg)
            print(f"[{self.account_name}] [SMTP OK] Email sent successfully from {self.email_user} to {to}")

            # Save to Sent folder via IMAP APPEND
            self._save_to_sent_folder(msg)

            return True
        except smtplib.SMTPRecipientsRefused as e:
            print(f"[{self.account_name}] [SMTP ERROR] Recipient refused: {e}")
            return False
        except smtplib.SMTPSenderRefused as e:
            print(f"[{self.account_name}] [SMTP ERROR] Sender refused: {e}")
            return False
        except smtplib.SMTPDataError as e:
            print(f"[{self.account_name}] [SMTP ERROR] Data error: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"[{self.account_name}] [SMTP ERROR] SMTP exception: {e}")
            return False
        except Exception as e:
            print(f"[{self.account_name}] [SMTP ERROR] Unexpected error: {type(e).__name__}: {e}")
            return False

    def _save_to_sent_folder(self, msg) -> bool:
        """Save sent email to Sent folder via IMAP APPEND.
        Connects with the inbox credentials to save to that inbox's Sent folder.
        """
        try:
            # Connect to IMAP with this inbox's credentials
            imap_sent = imaplib.IMAP4_SSL(EMAIL_HOST, IMAP_PORT)
            imap_sent.login(self.email_user, self.email_password)

            # Try common Sent folder names (Roundcube/FreeParking variants)
            sent_folders = ["Sent", "INBOX.Sent", "Sent Items", "Sent Messages"]

            for folder in sent_folders:
                try:
                    # Append message to Sent folder with \Seen flag
                    result = imap_sent.append(
                        folder,
                        "\\Seen",
                        None,
                        msg.as_bytes()
                    )
                    if result[0] == "OK":
                        print(f"[{self.account_name}] [SENT SAVED] Auto-reply saved to '{folder}' folder")
                        imap_sent.logout()
                        return True
                except Exception as e:
                    # Try next folder name
                    continue

            print(f"[{self.account_name}] [SENT] Could not find Sent folder, tried: {sent_folders}")
            imap_sent.logout()
            return False

        except Exception as e:
            print(f"[{self.account_name}] [SENT ERROR] Failed to save to Sent folder: {e}")
            return False

    def notify_escalation(self, email_data: Dict, intent: str):
        """Notify staff about escalated email - DO NOT auto-send reply."""
        sender_name = email_data.get("sender_name", email_data["sender"].split("@")[0].title())

        notification = EMAIL_TEMPLATES["escalation_notification"].format(
            sender=email_data["sender"],
            subject=email_data["subject"],
            intent=intent,
            body=email_data["body"][:500],
            name=sender_name
        )

        # Generate draft reply (for human to review/send)
        draft_reply = EMAIL_TEMPLATES.get("escalation_draft", "").format(
            name=sender_name,
            phone=GYM_INFO["phone"]
        )

        # Log escalation with draft
        self.log["escalations"].append({
            "timestamp": datetime.now().isoformat(),
            "sender": email_data["sender"],
            "sender_name": sender_name,
            "subject": email_data["subject"],
            "intent": intent,
            "body": email_data["body"][:200],
            "draft_reply": draft_reply,
            "status": "pending_review"
        })
        save_email_log(self.log)

        print(f"\n{'='*60}")
        print(notification)
        print(f"{'='*60}\n")

    def process_email(self, email_data: Dict) -> Dict:
        """Process a single email: classify, respond or escalate."""
        # Classify intent
        intent, action, confidence = self.classify_intent(email_data)

        result = {
            "email": email_data,
            "intent": intent,
            "action": action,
            "confidence": confidence,
            "response_sent": False,
            "timestamp": datetime.now().isoformat()
        }

        if action == "auto_reply":
            # Generate and send response
            response = self.generate_response(email_data, intent)
            if response:
                result["draft_response"] = response
                # LIVE MODE - Actually send the email
                success = self.send_email(email_data["sender_email"], "", response, email_data["subject"])
                result["response_sent"] = success
                if success:
                    print(f"[AUTO-REPLY SENT] {intent} -> {email_data['sender_email']}")
                else:
                    print(f"[AUTO-REPLY FAILED] {intent} -> {email_data['sender_email']} (check SMTP logs above)")
            self.log["stats"]["auto_replied"] += 1

        elif action == "escalate":
            self.notify_escalation(email_data, intent)
            self.log["stats"]["escalated"] += 1

        else:  # ignore
            print(f"[IGNORED] {intent} <- {email_data['sender_email']}")
            self.log["stats"]["ignored"] += 1

        self.log["stats"]["total"] += 1
        self.log["processed"].append(result)
        save_email_log(self.log)

        return result

    def process_inbox(self, limit: int = 10) -> List[Dict]:
        """Process unread emails from inbox."""
        emails = self.fetch_unread_emails(limit=limit)
        results = []

        for email_data in emails:
            result = self.process_email(email_data)
            # Mark as read after processing to prevent re-processing
            self.mark_as_read(email_data)
            results.append(result)

        return results


# Demo functions for testing without live email
def demo_process_email(subject: str, body: str, sender: str = "test@example.com") -> Dict:
    """Process a demo email without IMAP/SMTP."""
    bot = EmailBot()

    email_data = {
        "subject": subject,
        "sender": sender,
        "sender_name": sender.split("@")[0].title(),
        "sender_email": sender,
        "body": body,
        "date": datetime.now().isoformat(),
        "timestamp": datetime.now().isoformat()
    }

    return bot.process_email(email_data)


def get_stats() -> Dict:
    """Get email processing statistics."""
    log = load_email_log()
    return log.get("stats", {})


def get_escalations() -> List[Dict]:
    """Get list of escalated emails."""
    log = load_email_log()
    return log.get("escalations", [])
