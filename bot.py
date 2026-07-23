import logging
# import sqlite3
import requests
import mysql.connector


from telegram import ForceReply, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# # Define a few command handlers. These usually take the two arguments update and
# # context.
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Send a message when the command /start is issued."""
#     user = update.effective_user
#     await update.message.reply_html(
#         rf"Hi {user.mention_html()}!",
#         reply_markup=ForceReply(selective=True),
#     )

# Set up the SQLite database
def init_db():
    conn = mysql.connector.connect(host='localhost', user='root', password='Ab@123456789', database='tabibak')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            Id VARCHAR(255) PRIMARY KEY,
            Telegram_ID VARCHAR(255),
            Credit INT NOT NULL,
            Total_Cost FLOAT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            User_Id VARCHAR(255) NOT NULL,
            Telegram_Id VARCHAR(255),
            Chat_Id VARCHAR(255) NOT NULL,
            Type VARCHAR(255) NOT NULL,
            Message TEXT NOT NULL,
            Cost FLOAT NOT NULL,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()  # تغییرات را ذخیره کنید
    cursor.close()  # بستن کرسر
    conn.close()  # بستن اتصال

def create_chat(bot_id,user):
    url = 'https://api.metisai.ir/api/v1/chat/session'
    headers = {
        'Authorization': 'Bearer tpsg-47HeARQoxoAeFnz1aIXtX0JohAEyRLb',
        'Content-Type': 'application/json'
    }
    data = {
        "botId": "a0377f30-3518-4fcc-bd15-70600d4c5f83",
        "user": None,
        "initialMessages": [
            {
                "type": "USER",
                "content": "سلام"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()  # Check for HTTP errors

        # Parse the JSON response
        response_json = response.json()

        # Access the 'id'
        id_value = response_json.get('id', )


    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except ValueError:
        print("Response not in JSON format or is empty")
    except Exception as err:
        print(f"An error occurred: {err}")
        print(f"An error occurred: {err}")
    return id_value

def send_message(session_id,msg):
    # Replace with your actual session ID and API key
    api_key = "tpsg-47HeARQoxoAeFnz1aIXtX0JohAEyRLb"

    url = f'https://api.metisai.ir/api/v1/chat/session/{session_id}/message'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "message": {
            "content": msg,
            "type": "USER"
        }
    }

    response = requests.post(url, headers=headers, json=data)

    try:
            response.raise_for_status()  # Check for HTTP errors

            # Parse the JSON response
            response_json = response.json()

            # Access the 'id'
            response_msg = response_json.get('content', )
            response_cost = response_json.get('billing').get('cost')

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except ValueError:
        print("Response not in JSON format or is empty")
    except Exception as err:
        print(f"An error occurred: {err}")
        print(f"An error occurred: {err}")
    return response_msg,response_cost

# Function to create a custom keyboard menu
def create_menu():
    return ReplyKeyboardMarkup(
        [["سؤال از طبیبک 👩‍⚕️","وضعیت اعتبار 💳"]],
        resize_keyboard=True,  # Adjust size of buttons to fit screen
        one_time_keyboard=True  # Keyboard disappears after pressing a button
    )

# Function to create a custom keyboard menu
def create_chat_menu():
    return ReplyKeyboardMarkup(
        [['فعلاً سؤالی ندارم ↩️']],
        resize_keyboard=True,  # Adjust size of buttons to fit screen
        one_time_keyboard=True  # Keyboard disappears after pressing a button
    )


# Function to retrieve habits based on a given user ID
def get_credit_by_id(user_id):
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',  # آدرس سرور MySQL
        user='root',  # نام کاربری MySQL
        password='1234',  # رمز عبور MySQL
        database='tabibak'  # نام دیتابیس
    )
    cursor = conn.cursor()

    # Query to get the Credit column for the given ID
    cursor.execute("SELECT Credit FROM users WHERE ID = %s", (user_id,))
    
    # Fetch the first row that matches the query
    credits = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Check if any credits were found
    return credits[0] if credits else None

def update_credit_by_id(user_id, new_credit):
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',  # آدرس سرور MySQL
        user='root',  # نام کاربری MySQL
        password='1234',  # رمز عبور MySQL
        database='tabibak'  # نام دیتابیس
    )
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute('SELECT Id FROM users WHERE Id = %s', (user_id,))
    result = cursor.fetchone()

    # If the user exists, update their credit
    if result:
        cursor.execute('UPDATE users SET Credit = %s WHERE Id = %s', (new_credit, user_id))
        conn.commit()

    # Close the database connection
    conn.close()

# Function to insert or update a user's name in the database
def save_message(user_id, telegram_id, chat_id, type, message, message_cost):
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',  # آدرس سرور MySQL
        user='root',  # نام کاربری MySQL
        password='1234',  # رمز عبور MySQL
        database='tabibak'  # نام دیتابیس
    )
    cursor = conn.cursor()

    # Fetch the total cost for the user
    cursor.execute("SELECT Total_Cost FROM users WHERE ID = %s", (user_id,))
    total_cost = cursor.fetchone()

    if total_cost:
        new_cost = total_cost[0] + message_cost

        # Insert the new message into the messages table
        cursor.execute('INSERT INTO messages (User_Id, Telegram_Id, Chat_Id, Type, Message, Cost) VALUES (%s, %s, %s, %s, %s, %s)', 
                       (user_id, telegram_id, chat_id, type, message, message_cost))

        # Update the user's total cost
        cursor.execute('UPDATE users SET Total_Cost = %s WHERE ID = %s', (new_cost, user_id))

        # Commit the changes
        conn.commit()

    # Close the database connection
    conn.close()


# Function to insert or update a user's name in the database
def save_user(user_id, user_telegram_id, initial_credit):
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',  # آدرس سرور MySQL
        user='root',  # نام کاربری MySQL
        password='1234',  # رمز عبور MySQL
        database='tabibak'  # نام دیتابیس
    )
    cursor = conn.cursor()

    # Check if the user already exists in the database
    cursor.execute('SELECT Id FROM users WHERE Id = %s', (user_id,))
    if cursor.fetchone() is None:
        # Insert new user if not already in the database
        cursor.execute('INSERT INTO users (Id, Telegram_ID, Credit, Total_Cost) VALUES (%s, %s, %s, %s)', 
                       (user_id, user_telegram_id, initial_credit, 0))
    else:
        # Update user's Telegram ID if already exists
        cursor.execute('UPDATE users SET Telegram_ID = %s WHERE Id = %s', (user_telegram_id, user_id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


# Function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """
سلام 🖐
به بات طبیبک خوش اومدی ☺️
طبیبک، یه طبیب کوچیک ولی باحوصله و درس‌خونه!🤓
طبیبکِ ما، نشسته و با کلی پشتکار و شوق و ذوق، یه عالمه از به‌روزترین منابع پزشکی زنان رو مطالعه کرده.👩‍⚕️ الآن هم بی‌صبرانه آماده و مشتاقِ صحبت با یه طبیب واقعی مثل توئه تا با کمک هوشِ مصنوعیش کمکت کنه تا سؤالاتی که در مسیر طبابتت بهشون برمی‌خوری رو جواب بده. پس بیشتر از این منتظرش نذار و سرِ صحبتو باهاش باز کن!
راستی برای این‌که بیشتر در جریان حال‌واحوال و شیوهٔ کار با طبیبک باشی، لطفا حتماً در کانالِ تلگرام طبیبک (https://t.me/Tabibak_channel) عضو شو.
"""
    await update.message.reply_text(txt,reply_markup=create_menu())
    # Set up a next step to listen for the user's name
    # context.user_data['awaiting_name'] = True
    user_id = update.message.from_user.id
    telegram_user_id = update.message.from_user.username
    # Save the user's name and ID in the database
    save_user(user_id, telegram_user_id, 10)


# Function to handle messages (for capturing the name)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    user_id = update.message.from_user.id
    telegram_user_id = update.message.from_user.username

    if message_text == "سؤال از طبیبک 👩‍⚕️":
        credit = get_credit_by_id(user_id)

        if (credit > 0):
            txt = """
سلام 😍
من طبیبکم و خیلی دوست دارم که تو مسائل پزشکی بهت کمک کنم.
من تا الان تونستم در مباحث زیر مطالعه داشته باشم.

📌علل و درمان (PALM-COEIN) AUB.
📌خونریزی‌های غیر طبیعی در نیمه اول بارداری.
📌درمان PCO.
📌درمان هاپرپرولاکتینمی.
📌 داروهای ضد‌بارداری COC.

لطفا سؤالت رو از مباحثی که خوندم، برام بنویس تا زود، تند و سریع مقالاتِ روز رو بگردم و جوابت رو بهت بدم 📚 مثلاً میتونی این‌طوری بپرسی:
❓درمان های دارویی آدنومیوز رو فقط کوتاه نام ببر.
یا
❓خانمی بیست ساله پرولاکتین بالا داره. ازدواج نکرده. چه دارویی دقیقاً برایش تجویز کنم؟

راستی برای این‌که بهتر بتونی سؤالت رو مطرح کنی، پیشنهادم اینه که حتماً کانالم (https://t.me/Tabibak_channel) رو ببینی.
"""
            await update.message.reply_text(txt,reply_markup = create_chat_menu())
            context.user_data['get_case'] = True
        else:
            txt = """
طبیبک رفته تو اتاقش و داره گریه می‌کنه😭؛‌ می‌دونی چرا؟ 🤔
چون متأسفانه اعتبارت تموم شده و نمی‌تونه دیگه باهات حرف بزنه. برای افزایش اعتبارت، می‌تونی همین الآن دکمهٔ «وضعیت اعتبار» رو بزنی و زودتر طبیبک رو از ناراحتی دربیاری 😊👇"""
            await update.message.reply_text(txt,reply_markup=create_menu())      
    elif 'get_case' in context.user_data and context.user_data['get_case']:
        if message_text == "فعلاً سؤالی ندارم ↩️":
            context.user_data['get_case'] = False
            txt = """
چه کاری از دست طبیبک 👩‍⚕️ برمیاد؟
"""
            await update.message.reply_text(txt,reply_markup=create_menu())
        else:
            context.user_data['get_case'] = False
            session_id = create_chat("a0377f30-3518-4fcc-bd15-70600d4c5f83",None)
            credit = get_credit_by_id(user_id)
            update_credit_by_id(user_id,credit - 1)
            save_message(user_id,telegram_user_id,session_id,"User",message_text,0)
            reply_text,message_cost = send_message(session_id,message_text)
            save_message(user_id,telegram_user_id,session_id,"AI",reply_text,message_cost)
            await update.message.reply_text(reply_text,reply_markup=create_menu())
            

    elif message_text == "وضعیت اعتبار 💳":
        current_credit = get_credit_by_id(user_id)
        txt = """تو میتونی با مقدار اعتبار فعلیت، {} سوال دیگه از طبیبک👩‍⚕️بپرسی.
اگر می‌خوای اعتبارت رو افزایش بدی، می‌تونی به پشتیبان طبیبک (@Tabibak_support) پیام بدی ☺️
""".format(str(current_credit))
        
        await update.message.reply_text(txt,reply_markup=create_menu())

    else:
        # Handle other messages (if needed)
        txt = """
طبیبک نفهمید چی گفتی 🤔
برای شروع دوبارهٔ طبیبک 👩‍⚕️ همین الآن /start رو بزن.
"""
        await update.message.reply_text(txt)

def main() -> None:
    """Start the bot."""

    init_db()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7843740103:AAG6XWiV1f2WSlHqGSZYI_cZ8VGXfYZtoVs").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()