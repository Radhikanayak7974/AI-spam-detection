"""
Builds a comprehensive benchmark spam/ham email dataset.
Generates balanced, representative email messages across common spam vectors and normal business/personal communications.
"""

import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "spam_dataset.csv")

# Templates for realistic spam emails
SPAM_TEMPLATES = [
    "URGENT: Your account at {bank} has been suspended due to suspicious activity. Click {url} immediately to verify your identity and restore access.",
    "Congratulations! You have been selected as the winner of our {year} international sweepstakes prize of ${amount}. Call now at {phone} to claim your prize.",
    "Dear Customer, your invoice #{inv_id} for the amount of ${amount} is ready for download. Please open the attached document or click {url} to pay.",
    "Exclusive Offer: Get {discount}% discount on all luxury watches and prescription medications! Limited time only at {url}.",
    "SECURITY ALERT: We detected an unauthorized login to your email from an unknown IP address ({ip}). Verify your password now at {url}.",
    "Make ${amount} per day working from home! No experience required. Guaranteed daily payout. Sign up right now at {url}.",
    "Final Notice: Your package delivery #{track_id} is on hold due to missing address details. Pay $2.99 customs fee at {url} to release delivery.",
    "Hi, I am a foreign diplomat handling an unclaimed inheritance of ${amount}M. I need your assistance to transfer these funds. Reply with your passport copy.",
    "Investment opportunity: Guaranteed {rate}% returns on Bitcoin mining! Don't miss out on this life-changing passive income. Register at {url}.",
    "You have (1) pending tax refund of ${amount} from the Revenue Service. Submit your direct deposit details at {url} within 24 hours.",
    "Dear user, your mailbox storage is 99% full. Incoming messages will be bounced. Upgrade storage for free at {url}.",
    "Hot singles in your area want to chat with you right now! Click here {url} to view private profiles for free.",
    "Your Netflix membership is expiring today. Update your payment card details now at {url} to continue streaming without interruption.",
    "PayPal Security: We noticed unusual activity on your credit card. Your account is temporarily limited. Confirm your SSN and PIN at {url}.",
    "Pre-approved loan up to ${amount} with 0% interest rate for the first 12 months! Fast approval in 10 minutes. Apply here: {url}",
    "URGENT: Claim your $500 Amazon Gift Card reward now! Complete this quick 2-minute survey before it expires: {url}.",
    "Dear Beneficiary, this is Western Union payment office. We have an approved money transfer of ${amount} waiting for you. Send your address to proceed.",
    "Crypto Whale Alert: Join our VIP Telegram pump signal group and multiply your portfolio 10x this week! Link: {url}.",
    "Immediate Action Required: Your antivirus subscription #{inv_id} auto-renewed for ${amount}. Call our toll-free support {phone} to cancel.",
    "Secret shopping assignment: Earn ${amount} weekly evaluating local stores. We will send you an upfront cashier check. Reply to apply.",
]

# Templates for realistic safe/ham emails
HAM_TEMPLATES = [
    "Hi team, just a reminder that our weekly sprint planning meeting is scheduled for tomorrow at {time} in room {room}. Please update your Jira tickets.",
    "Attached is the revised Q3 financial report for your review. Let me know if you have any questions or require additional breakdowns.",
    "Hey {name}, are you free for lunch today around {time}? We were thinking of checking out the new Mediterranean place down the street.",
    "Thank you for reaching out to support. We have received your inquiry #{ticket_id} and our technical team is investigating the issue.",
    "Hi all, please find the meeting notes and action items from today's sync attached. Next follow-up is scheduled for next Tuesday.",
    "Dear {name}, your flight confirmation for booking #{pnr} has been issued. Boarding begins at {time}. Have a pleasant trip!",
    "Hi, can you please review the pull request for the authentication service when you get a chance? I've addressed all comments from yesterday.",
    "Reminder: The office will be closed on Monday in observance of the public holiday. Please ensure all urgent tasks are wrapped up by Friday.",
    "Hi {name}, I've uploaded the high-fidelity Figma mockups for the dashboard redesign. Looking forward to your feedback during design review.",
    "Your monthly electric utility statement for account #{acct_id} is now available online. Total due: ${small_amount} by the end of the month.",
    "Hello team, the production database maintenance has completed successfully with zero downtime. All services are operating normally.",
    "Hi {name}, here are the slides from today's presentation on machine learning pipelines. Feel free to share them with the rest of the department.",
    "Thanks for connecting on LinkedIn, {name}. It was great meeting you at the tech conference last week. Let's keep in touch!",
    "Hi, please find the receipt for your recent Uber trip. Fare: ${small_amount}. If you have questions regarding this trip, visit help.uber.com.",
    "Dear customer, your order #{order_id} has been dispatched and is on track for delivery on Wednesday. You can track your shipment anytime.",
    "Good morning everyone, please welcome Sarah to our engineering team as our new senior backend developer. She joins us from Acme Corp.",
    "Hi {name}, could you send over the vendor contract draft when it's finalized? Legal needs to sign off before the end of the quarter.",
    "Just wanted to follow up on our discussion regarding the client proposal. Do you think we can finalize the pricing structure by Thursday?",
    "Hey, the quarterly company all-hands meeting will be held virtually on Zoom next Thursday at {time}. The agenda will follow shortly.",
    "Your annual health checkup appointment is confirmed with Dr. Smith for next Friday at {time}. Please arrive 15 minutes early.",
]

def generate_dataset(num_samples=1200):
    banks = ["Chase", "Wells Fargo", "Bank of America", "Citibank", "Barclays", "Capital One"]
    names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "David", "Emma", "Liam"]
    urls = [
        "http://bit.ly/secure-verify392",
        "http://bank-verification-portal.xyz/login",
        "http://account-recovery-security.info",
        "http://free-gift-prizes.net/claim",
        "http://update-billing-profile.cc/auth",
        "http://urgent-notice-online.me/verify",
    ]
    random.seed(42)

    rows = []
    
    # 1. Generate Spam samples (approx 45%)
    num_spam = int(num_samples * 0.45)
    for i in range(num_spam):
        tpl = random.choice(SPAM_TEMPLATES)
        text = tpl.format(
            bank=random.choice(banks),
            year=random.choice(["2025", "2026"]),
            amount=random.choice(["5,000", "25,000", "150,000", "2,500,000", "950"]),
            phone=f"+1-800-{random.randint(100,999)}-{random.randint(1000,9999)}",
            inv_id=f"INV-{random.randint(10000, 99999)}",
            url=random.choice(urls),
            discount=random.choice(["50", "70", "85", "90"]),
            ip=f"{random.randint(10,220)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            track_id=f"PKG-{random.randint(100000, 999999)}",
            rate=random.choice(["200", "350", "500"]),
        )
        # Add slight variations
        if random.random() < 0.2:
            text = "Fwd: " + text
        elif random.random() < 0.2:
            text = text + " Unsubscribe here."
        rows.append({"label": "spam", "text": text})

    # 2. Generate Ham samples (approx 55%)
    num_ham = num_samples - num_spam
    for i in range(num_ham):
        tpl = random.choice(HAM_TEMPLATES)
        text = tpl.format(
            name=random.choice(names),
            time=random.choice(["10:00 AM", "2:30 PM", "11:15 AM", "4:00 PM"]),
            room=random.choice(["Conference Room B", "Auditorium 2", "Hudson Boardroom"]),
            ticket_id=f"TCK-{random.randint(1000, 9999)}",
            pnr=f"PNR{random.randint(10000, 99999)}",
            small_amount=f"{random.randint(15, 140)}.{random.randint(10, 99)}",
            acct_id=f"ACC-{random.randint(100000, 999999)}",
            order_id=f"ORD-{random.randint(100000, 999999)}",
        )
        if random.random() < 0.2:
            text = "Re: " + text
        rows.append({"label": "ham", "text": text})

    # Shuffle dataset
    random.shuffle(rows)

    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    with open(DATASET_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "text"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[Dataset] Generated {len(rows)} samples ({num_spam} spam, {num_ham} ham) at {DATASET_PATH}")
    return len(rows)

if __name__ == "__main__":
    generate_dataset()
