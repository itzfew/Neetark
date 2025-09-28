import json
import os
import random

def load_questions(data_dir='data'):
    """
    Load all subject JSON files into a dict: {subject: [questions]}
    Each question: {"question": str, "options": {"A": str, ...}, "answer": str}
    """
    subjects = {}
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created {data_dir} folder. Add JSON files there.")
        return subjects
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            subject = filename[:-5]
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    subjects[subject] = json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading {filepath}")
    return subjects

def get_random_question(subjects):
    """Get a random question from a random subject."""
    if not subjects:
        return None
    subject = random.choice(list(subjects.keys()))
    questions = subjects[subject]
    q = random.choice(questions)
    return {
        "subject": subject,
        "question": q["question"],
        "options": q["options"],
        "answer": q["answer"]
    }

def format_quiz_message(quiz_data):
    """Format the quiz as a Telegram message."""
    msg = f"🧠 Quiz Time! Subject: {quiz_data['subject'].upper()}\n\n"
    msg += f"{quiz_data['question']}\n\n"
    for opt, text in quiz_data['options'].items():
        msg += f"{opt}) {text}\n"
    msg += "\nReply with A, B, C, or D to answer! ⏰"
    return msg

def get_correct_response(current_score):
    """Random funny correct response with score update."""
    messages = [
        f"🎉 . 😂 Waah bhai, NCERT tumhe apna damaad banane wali hai! +4 points!\nYour score: {current_score}",
        f"🚀 . 😎 Sahi ja raha hai, future doctor! +4 points!\nYour score: {current_score}",
        f"💯 . 🔥 Perfect! Tu to NEET crack kar dega! +4 points!\nYour score: {current_score}"
    ]
    return random.choice(messages)

def get_wrong_response(current_score):
    """Random funny wrong response with score update."""
    messages = [
        f"😔 . 🤕 Thoda aur mehnat! -1 point\nYour score: {current_score}",
        f"😔 . 🫠 Bhai tu doctor banega ya RJ Naved?! -1 point\nYour score: {current_score}",
        f"😂 . 😅 Galat ho gaya, par try again! -1 point\nYour score: {current_score}"
    ]
    return random.choice(messages)
