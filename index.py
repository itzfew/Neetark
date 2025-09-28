import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os
from quiz import load_questions, get_random_question, format_quiz_message, get_correct_response, get_wrong_response

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

# Ensure single instance of polling
polling_thread = None

def clear_webhook():
    """Clear any existing webhook to ensure polling works."""
    try:
        bot.remove_webhook()
        print("Webhook cleared successfully.")
    except Exception as e:
        print(f"Error clearing webhook: {e}")

def send_quiz(chat_id):
    """Send a random quiz to a group."""
    quiz_data = get_random_question(subjects)
    if not quiz_data:
        bot.send_message(chat_id, "❌ No questions loaded! Add data/*.json files.")
        return
    
    try:
        message = format_quiz_message(quiz_data)
        sent_msg = bot.send_message(chat_id, message)
        
        active_quizzes[chat_id] = {
            "answer": quiz_data["answer"],
            "answered": set()
        }
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending quiz to {chat_id}: {e}")
        if "chat not found" in str(e).lower() or "blocked by user" in str(e).lower():
            groups.discard(chat_id)

def send_quiz_to_all():
    """Send quiz to all subscribed groups."""
    for chat_id in list(groups):
        try:
            send_quiz(chat_id)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")
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
    
    try:
        if user_answer == quiz["answer"]:
            new_score = current_score + 4
            response = get_correct_response(new_score)
            user_scores[user_id] = new_score
        else:
            new_score = current_score - 1
            response = get_wrong_response(new_score)
            user_scores[user_id] = new_score
        
        bot.reply_to(message, response)
    except Exception as e:
        print(f"Error handling answer for {chat_id}: {e}")
        bot.reply_to(message, "⚠️ Error processing your answer. Try again!")

# Scheduler setup
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_quiz_to_all, 'interval', minutes=30)
    scheduler.start()
    print("Scheduler started.")

def start_polling():
    """Start polling with error handling and single instance check."""
    global polling_thread
    if polling_thread and polling_thread.is_alive():
        print("Polling already running.")
        return
    
    clear_webhook()  # Clear any existing webhook before polling
    try:
        polling_thread = threading.Thread(target=bot.infinity_polling, args=(True, 1))
        polling_thread.daemon = True
        polling_thread.start()
        print("Bot polling started.")
    except Exception as e:
        print(f"Error starting polling: {e}")

if __name__ == "__main__":
    print("Starting NEETARK bot...")
    start_scheduler()
    start_polling()
