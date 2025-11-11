import os
import time
import random
import schedule

import firebase_admin
from firebase_admin import credentials, messaging

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

# CONFIG LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)

cred = credentials.Certificate("serviceAccount.json")

# Initialize Firebase
firebase_admin.initialize_app(cred)

FCM_TOPIC = "testing-notification"
ANDROID_CHANNEL_ID = "bible_reminders"


# BASE DATA 
TITLES = [
    "Blessing",
    "Prayer Pause",
    "Reflection in the Lord",
    "God’s Word for You",
    "Strength from Scripture",
    "Faith Over Fear",
    "Encouragement",
    "Christ-Focused Mind",
    "Walk in His Light",
    "Grace Reminder",
    "Time to Pray",
    "Bible Moment",
    "Hope in Christ",
    "Thankful Heart",
    "Prepare Your Heart",
    "Quiet Heart, Strong Faith",
    "Inspiration",
    "Renewed Mind",
    "Peace Within",
    "Stand Firm in Faith",
    "God’s Love Never Fails",
    "Be Still and Know",
    "Let Your Light Shine",
    "Rejoice in the Lord",
    "Scripture Spark",
    "Grace for You",
    "Faith Fuel",
    "Hope Restored",
    "Journey with Jesus",
    "Spirit Recharge",
    "Bible Study Reminder",
    "Blessings Overflow",
    "Pray Without Ceasing",
    "Faith Check-In",
    "Lift Your Eyes",
    "Strength in Prayer",
    "Scripture Focus",
    "God’s Promise",
    "Stay Rooted in Christ",
    "Praise Break",
    "Heart of Gratitude",
    "Wisdom Whisper",
    "Faith Boost",
    "Rest in Christ",
    "Joyful Spirit",
    "God Is With You",
    "Hope in the Lord",
    "Spirit of Thankfulness",
    "Keep Trusting",
    "New Mercies"
]
CONTENTS = [
    "Remember to pray and bring your plans to God — He delights in hearing you.",
    "A short verse can shape your whole outlook. Open the Scriptures and receive.",
    "Gratitude opens the door to joy. Take a moment to thank God.",
    "You are not alone. The Lord walks beside you in every season.",
    "Speak a prayer of peace. Even a quiet cry is heard in heaven.",
    "Feed your faith and your fears will lose strength.",
    "Pause and read Psalm 23. Let the Shepherd calm your heart.",
    "Breathe and rest — God is in control of every detail.",
    "Your prayer can move mountains because God is able.",
    "Reflect on God’s promises and let hope rise again.",
    "Show kindness; it is a simple way to reflect Christ.",
    "Cast your worries on Him, because He truly cares for you.",
    "When you feel weak, remember His strength is made perfect in weakness.",
    "Let your actions show the love of Christ to the people around you.",
    "Pray for someone who needs comfort and encouragement.",
    "God’s plan is greater than any frustration you face.",
    "A tender heart is good soil for the word of God.",
    "Choose peace instead of anger; it is the fruit of the Spirit.",
    "The Bible is not just a book — it is God’s loving message to you.",
    "Set aside a few quiet minutes and listen for His voice.",
    "Meditate on Proverbs 3:5-6 and trust the Lord fully.",
    "Give thanks for a few small blessings God has provided.",
    "Ask God to renew your mind with truth and clarity.",
    "Let joy, not anxiety, lead your heart.",
    "You are God’s workmanship, created with purpose.",
    "Hold on to one verse and think about it throughout your activities.",
    "Forgive quickly and keep a life of prayer.",
    "Bless someone without expecting anything in return.",
    "Praise shifts your focus from the problem to the Provider.",
    "Turn worry into worship; God meets you there.",
    "God loves to hear your voice — speak to Him now.",
    "Pray for wisdom before you make decisions.",
    "The same God who parted seas can open the path before you.",
    "Do not rush; slow down and thank God for life.",
    "Remember His past faithfulness to trust Him for what is ahead.",
    "Hold on to the promise of Jesus: He is always with you.",
    "Fill your soul with Scripture before you fill your schedule.",
    "Speak faith, not fear — your words carry life.",
    "Let your home be filled with praise and worship.",
    "God’s timing is perfect, even when it feels delayed.",
    "Go to the Psalms when your heart is low; they lift the soul.",
    "Pray for your family by name; they need your intercession.",
    "Smile; your joy can remind someone of God’s hope.",
    "A few quiet moments with God can realign your whole heart.",
    "Keep believing — God often works in gentle, hidden ways.",
    "Choose gratitude over grumbling.",
    "Whisper a prayer for peace over the nations.",
    "Read a verse of encouragement and let it settle in you.",
    "Ask the Holy Spirit to guide your steps and your words.",
    "Thank God for His mercies that never run out."
]

MESSAGES = [
    {"title": t, "body": c} for t, c in zip(TITLES, CONTENTS)
]


def rewrite_with_llm(title: str, body: str) -> tuple[str, str]:
    print('Rewritting Notification Message....')
    prompt = (
        "You help a Christian mobile app send short devotional push notifications.\n"
        "Rewrite the following message to be 1–2 sentences, under 130 characters, "
        "sound encouraging, and keep it Bible/prayer/Christian related. "
        "Do not add emojis.\n\n"
        f"Title: {title}\n"
        f"Message: {body}\n"
        "Return ONLY the rewritten message text."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=80,
    )

    rewritten = resp.choices[0].message.content.strip().replace("\n", " ")

    return title, rewritten


def send_notification(title: str, body: str):
    print('Sending Notification...')
    message = messaging.Message(
        topic=FCM_TOPIC,
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id=ANDROID_CHANNEL_ID
            )
        )
    )
    resp = messaging.send(message)
    print(f"[FCM] sent: {resp} -> {title} | {body}")


def run_agent_once():
    print('AiO Agent: Sending notification now...')
    base_msg = random.choice(MESSAGES)
    print("[agent] picked base:", base_msg)

    try:
        final_title, final_body = rewrite_with_llm(base_msg["title"], base_msg["body"])
        print('Notification content finalized!')
    except Exception as e:
        print("[agent] LLM failed, using base:", e)
        final_title, final_body = base_msg["title"], base_msg["body"]

    print('Sending final Notification')
    send_notification(final_title, final_body)


# SCHEDULE
# schedule.every().day.at("06:00").do(run_agent_once)
# schedule.every().day.at("12:00").do(run_agent_once)
# schedule.every().day.at("18:00").do(run_agent_once)

schedule.every(1).minutes.do(run_agent_once)

if __name__ == "__main__":
    print("AiO Bible Agent started...")
    while True:
        schedule.run_pending()
        time.sleep(1)
