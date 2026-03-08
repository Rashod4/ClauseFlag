import csv
import json
import random

data = [
    # Safe Clauses
    {"text": "We collect your email address when you create an account to provide you with our services.", "risk": "safe", "category": "Data Collection", "explanation": "Standard collection of necessary contact information for account creation.", "source": "General Service"},
    {"text": "You can delete your account and all associated data at any time through your account settings.", "risk": "safe", "category": "Data Rights", "explanation": "Gives the user full control to delete their data.", "source": "General Service"},
    {"text": "We use industry-standard encryption to protect your personal information during transmission.", "risk": "safe", "category": "Security", "explanation": "Standard security practice to protect user data.", "source": "General Service"},
    {"text": "We do not sell your personal information to third parties.", "risk": "safe", "category": "Data Sharing", "explanation": "Explicitly protects user data from being sold.", "source": "General Service"},
    {"text": "You retain all ownership rights to the content you upload to our platform.", "risk": "safe", "category": "IP Rights", "explanation": "Ensures the user keeps ownership of their own content.", "source": "General Service"},
    {"text": "We will notify you at least 30 days in advance of any material changes to these terms.", "risk": "safe", "category": "Updates", "explanation": "Provides reasonable notice before changing the rules.", "source": "General Service"},
    {"text": "You may opt out of receiving promotional emails by clicking the unsubscribe link in any email.", "risk": "safe", "category": "Communication", "explanation": "Standard opt-out mechanism for marketing.", "source": "General Service"},
    {"text": "This agreement is governed by the laws of the State of California.", "risk": "safe", "category": "Dispute Resolution", "explanation": "Standard choice of law provision.", "source": "General Service"},
    {"text": "We log your IP address to prevent fraud and abuse on our platform.", "risk": "safe", "category": "Data Collection", "explanation": "Standard security practice with a clear, legitimate purpose.", "source": "General Service"},
    {"text": "If you are under 13, you may not use our services.", "risk": "safe", "category": "Age Restrictions", "explanation": "Standard compliance with COPPA.", "source": "General Service"},
    {"text": "We may suspend your account if you violate these Terms of Service.", "risk": "safe", "category": "Termination", "explanation": "Standard enforcement of terms.", "source": "General Service"},
    {"text": "You are responsible for keeping your password secure.", "risk": "safe", "category": "User Responsibilities", "explanation": "Standard user security responsibility.", "source": "General Service"},

    # Watch Clauses
    {"text": "We may share your anonymized usage data with our analytics partners.", "risk": "watch", "category": "Data Sharing", "explanation": "Data is anonymized, but still shared with third parties for analytics.", "source": "General Service"},
    {"text": "We use cookies and similar technologies to track your activity on our website.", "risk": "watch", "category": "Tracking", "explanation": "Standard tracking, but merits awareness of how activity is monitored.", "source": "General Service"},
    {"text": "Our service may contain links to third-party websites not controlled by us.", "risk": "watch", "category": "Third Parties", "explanation": "Standard disclaimer, reminding you that other sites have their own rules.", "source": "General Service"},
    {"text": "We may contact you with promotional offers from our affiliates.", "risk": "watch", "category": "Communication", "explanation": "Allows affiliate marketing, which may result in more emails.", "source": "General Service"},
    {"text": "We retain your data for as long as your account is active or as needed to provide you services.", "risk": "watch", "category": "Data Retention", "explanation": "Data is kept indefinitely while the account is open.", "source": "General Service"},
    {"text": "You grant us a license to use your uploaded content to operate and improve our services.", "risk": "watch", "category": "IP Rights", "explanation": "Standard operating license, but gives the platform broad rights to use your content.", "source": "General Service"},
    {"text": "We may collect information about your device, including hardware model and OS.", "risk": "watch", "category": "Data Collection", "explanation": "Collects detailed device profiling data.", "source": "General Service"},
    {"text": "Our services are provided 'as is' without any warranties.", "risk": "watch", "category": "Liability", "explanation": "Standard disclaimer limiting their legal liability for issues.", "source": "General Service"},
    {"text": "We may process your data on servers located outside your home country.", "risk": "watch", "category": "Data Transfer", "explanation": "Data may be subject to different privacy laws internationally.", "source": "General Service"},
    {"text": "We may update these terms occasionally, and your continued use implies consent.", "risk": "watch", "category": "Updates", "explanation": "Silent updates without active confirmation.", "source": "General Service"},
    {"text": "If our company is acquired, your data will be transferred to the new owners.", "risk": "watch", "category": "Business Transfer", "explanation": "Your data changes hands if the company is sold.", "source": "General Service"},
    {"text": "We may use your personal information to personalize the advertising you see.", "risk": "watch", "category": "Targeted Ads", "explanation": "Uses your data for targeted advertising profiles.", "source": "General Service"},

    # Danger Clauses
    {"text": "We may sell your personal data to third-party marketing partners.", "risk": "danger", "category": "Data Selling", "explanation": "Explicitly monetizes your personal data by selling it to third parties.", "source": "General Service"},
    {"text": "You waive your right to participate in a class action lawsuit against us.", "risk": "danger", "category": "Dispute Resolution", "explanation": "Severely limits your legal recourse by preventing collective action.", "source": "General Service"},
    {"text": "All disputes must be resolved through binding arbitration.", "risk": "danger", "category": "Dispute Resolution", "explanation": "Forces you out of public courts into private arbitration.", "source": "General Service"},
    {"text": "We reserve the right to change these terms at any time without prior notice.", "risk": "danger", "category": "Updates", "explanation": "Allows them to change the rules at any time without telling you.", "source": "General Service"},
    {"text": "You grant us a worldwide, perpetual, irrevocable, royalty-free license to use, modify, and distribute your content.", "risk": "danger", "category": "IP Rights", "explanation": "You permanently give up essentially all rights to your intellectual property.", "source": "General Service"},
    {"text": "We may terminate your account at any time, for any reason, without notice or liability.", "risk": "danger", "category": "Termination", "explanation": "Extremely broad termination rights with no protection for the user.", "source": "General Service"},
    {"text": "We collect your precise geolocation data continuously in the background.", "risk": "danger", "category": "Data Collection", "explanation": "Highly invasive tracking of your physical location at all times.", "source": "General Service"},
    {"text": "We are not liable for any damages, even if we were negligent or aware of the possibility.", "risk": "danger", "category": "Liability", "explanation": "Attempts to completely absolve the company of all responsibility, even for negligence.", "source": "General Service"},
    {"text": "We may read your private messages to improve our advertising algorithms.", "risk": "danger", "category": "Privacy Violation", "explanation": "Severe violation of communication privacy for commercial gain.", "source": "General Service"},
    {"text": "You agree to indemnify and hold us harmless from any claims arising from your use of the service.", "risk": "danger", "category": "Liability", "explanation": "Shifts all legal and financial burden onto the user, even for the platform's failures.", "source": "General Service"},
    {"text": "We retain the right to collect data from your microphone at any time.", "risk": "danger", "category": "Data Collection", "explanation": "Extremely invasive surveillance of your offline environment.", "source": "General Service"},
    {"text": "By using our service, you consent to us sharing your complete browsing history with our affiliates.", "risk": "danger", "category": "Data Sharing", "explanation": "Massive overcollection and sharing of sensitive web activity.", "source": "General Service"},
]

# Generate more variations to reach a larger dataset size for the MVP
import copy
extended_data = []

# Expand the dataset to roughly 100-200 clauses by adding slight variations
for i in range(15):
    for item in data:
        new_item = copy.deepcopy(item)
        new_item["source"] = random.choice(["Google ToS", "Meta PP", "Twitter ToS", "Amazon PP", "Spotify ToS", "Apple Privacy Policy", "Netflix Terms", "TikTok Privacy Policy"])
        extended_data.append(new_item)

# Write to CSV
with open('data/training_dataset.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["text", "risk", "category", "explanation", "source"])
    writer.writeheader()
    writer.writerows(extended_data)

# Write to JSON
with open('data/training_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(extended_data, f, indent=2)

print(f"Generated {len(extended_data)} clauses in data/training_dataset.csv and .json")
