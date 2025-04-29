import imaplib
import email
import time
import re
from typing import List

# === CONFIGURATION ===

IMPORTANT_SENDERS = []
KEYWORDS_SUBJECT = ["urgente"]

LOG_FILE = "email_log.txt"

# === FUNCTIONS ===
def connect():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def check_emails():
    try:
        mail = connect()
        mail.select("inbox")

        status, messages = mail.search(None, '(UNSEEN)')
        email_ids = messages[0].split()

        for eid in email_ids:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg["subject"] or "(sin asunto)"
            from_ = msg["from"]
            decoded_header = email.header.decode_header(subject)
            decoded_subject_parts = []
            #print(subject+" "+from_)
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    try:
                        decoded_subject_parts.append(part.decode(encoding or 'utf-8'))
                    except:
                        decoded_subject_parts.append(part.decode('latin1', errors='ignore'))
                else:
                    decoded_subject_parts.append(part)

            decoded_subject = ' '.join(decoded_subject_parts)


            if any(sender in from_ for sender in IMPORTANT_SENDERS) or \
               any(re.search(kw, decoded_subject, re.IGNORECASE) for kw in KEYWORDS_SUBJECT):
                notify(decoded_subject, from_)

        mail.logout()
        print("")
    except Exception as e:
        log(f"[ERROR] {e}")

def notify(subject: str, from_: str):
    log(f"Nuevo correo importante de {from_} | Asunto: {subject}")

def log(msg: str):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {msg}\n")

# === LOOP ===
if __name__ == "__main__":
    log("Iniciando email_checker...")
    while True:
        print("checking...")
        check_emails()
        time.sleep(CHECK_INTERVAL)
