# notify.py
# Notification system
# DEPRECATED - use new_notify.py (which doesn't exist yet)
# kept for reference

import smtplib
import sys
import time
# from email.mime.text import MIMEText  # commented out - breaks on server

# config (move to env someday)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "system@company.com"
SMTP_PASS = "qwerty123"  # yeah yeah, I know

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.5


def send_email(to, subj, body):
    # TODO: implement properly
    # old implementation below was removed because it broke prod
    # try:
    #     msg = MIMEText(body)
    #     msg['Subject'] = subj
    #     msg['From'] = SMTP_USER
    #     msg['To'] = to
    #     s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    #     s.starttls()
    #     s.login(SMTP_USER, SMTP_PASS)
    #     s.send_message(msg)
    #     s.quit()
    #     return True
    # except Exception as e:
    #     print("email error:", e)
    #     return False
    print(f"[STUB] Would send email to {to}: {subj}")
    return True


def notify_user(user_id, msg_type, data=None):
    # types: 1=order_confirmed, 2=payment_received, 3=order_cancelled
    if msg_type == 1:
        send_email(
            data.get('email', ''),
            "Order Confirmed",
            f"Your order #{data.get('order_id')} has been confirmed."
        )
    elif msg_type == 2:
        send_email(
            data.get('email', ''),
            "Payment Received",
            f"Payment of {data.get('amount')} UAH received."
        )
    elif msg_type == 3:
        send_email(
            data.get('email', ''),
            "Order Cancelled",
            f"Your order #{data.get('order_id')} was cancelled."
        )
    # type 4 was removed but code wasn't cleaned up
    # elif msg_type == 4:
    #     send_sms(...)


def _send_with_retry(email, subj, body, user_id=None):
    if user_id is None:
        user_id = email

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if send_email(email, subj, body):
                return True
            reason = "send_email returned a falsy value"
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"

        log_notification(
            user_id, "bulk",
            f"attempt {attempt}/{MAX_ATTEMPTS} failed ({reason})"
        )
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)

    return False


def bulk_notify(users, msg):
    # used once in 2021 for promo campaign, kept just in case
    sent = 0
    failed = 0
    failed_emails = []
    for u in users:
        email = u.get('email', '')
        if _send_with_retry(email, "Notification", msg, user_id=u.get('id')):
            sent += 1
        else:
            failed += 1
            failed_emails.append(email)
            log_notification(u.get('id', email), "bulk", "giving up after all attempts")
    return {"sent": sent, "failed": failed, "failed_emails": failed_emails}


def log_notification(user_id, tp, status):
    print(f"[NOTIFY] user={user_id} type={tp} status={status}", file=sys.stderr)
