import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import threading
from quiz import load_questions, get_random_question, format_quiz_message, get_correct_response, get_wrong_response
import os

# Bot setup
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("Set BOT_TOKEN environment variable!")

bot = telebot.TeleBot(TOKEN)

# Global state
subjects = load_questions()
groups = set()  # Subscribed group chat_ids
active_quizzes = {}  # {chat_id: {"answer": str, "answered": set(user_ids)}}
user_scores = {}  # {user_id: int}

def send_quiz(chat_id):
    """Send a random quiz to a group."""
    quiz_data = get_random_question(subjects)
    if not quiz_data:
        bot.send_message(chat_id, "❌ No questions loaded! Add data/*.json files.")
        return
    
    message = format_quiz_message(quiz_data)
    sent_msg = bot.send_message(chat_id, message)
    
    active_quizzes[chat_id] = {
        "answer": quiz_data["answer"],
        "answered": set()
    }

def send_quiz_to_all():
    """Send quiz to all subscribed groups."""
    for chat_id in list(groups):
        try:
            send_quiz(chat_id)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")
            if chat_id not in groups:
                groups.discard(chat_id)

# Handlers
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.chat.type in ['group', 'supergroup']:
        groups.add(chat_id)
        welcome = "🤖 Welcome to NEETARK! I'll send NEET quizzes every 30 mins. Reply to quizzes with A/B/C/D.\nUse /score to check your points."
        bot.reply_to(message, welcome)
    else:
        bot.reply_to(message, "👋 Hi! Add me to a group and type /start to subscribe to quizzes.")

@bot.message_handler(commands=['score'])
def score_handler(message):
    user_id = message.from_user.id
    score = user_scores.get(user_id, 0)
    bot.reply_to(message, f"📊 Your current score: {score} points")

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.reply_to_message and m.text and m.text.upper() in ['A', 'B', 'C', 'D'])
def quiz_answer_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_answer = message.text.upper().strip()
    
    if chat_id not in active_quizzes:
        bot.reply_to(message, "❓ No active quiz! Wait for the next one.")
        return
    
    quiz = active_quizzes[chat_id]
    if user_id in quiz["answered"]:
        bot.reply_to(message, "✅ You already answered this quiz!")
        return
    
    quiz["answered"].add(user_id)
    current_score = user_scores.get(user_id, 0)
    
    if user_answer == quiz["answer"]:
        new_score = current_score + 4
        response = get_correct_response(new_score)
        user_scores[user_id] = new_score
    else:
        new_score = current_score - 1
        response = get_wrong_response(new_score)
        user_scores[user_id] = new_score
    
    bot.reply_to(message, response)
    
    # Clean up if all answered (optional, but for now, keep until next quiz)

# Scheduler setup
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_quiz_to_all, 'interval', minutes=30)
    scheduler.start()

if __name__ == "__main__":
    print("Starting NEETARK bot...")
    start_scheduler()
    bot.infinity_polling(none_stop=True, interval=1)
