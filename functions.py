import openai
import pandas as pd
import os
import json
import sqlite3
from difflib import get_close_matches
from datetime import datetime, timedelta
import pytz
import threading


# Initialize SQLite database connection
conn = sqlite3.connect('restaurant.db')
c = conn.cursor()

tls = threading.local()

def get_db():
    # Check if there's already a Connection in this thread
    if not hasattr(tls, 'db'):
        # Create a new Connection for this thread
        tls.db = sqlite3.connect('restaurant.db')
    return tls.db


#Create reservations table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_number INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_date TEXT NOT NULL,
        reservation_time TEXT,
        name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        email_address TEXT NOT NULL,
        guests INTEGER NOT NULL,
        reservation_type TEXT NOT NULL,
        address TEXT,
        delivery_time TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()

# Load menu from CSV
def get_menu():
    """
    Retrieves the menu items from a CSV file.

    Returns:
    dict: A dictionary where keys are categories and values are lists of items.
    """

    menu_df = pd.read_csv('menu.csv')

    menu = menu_df.groupby('Section')['Item'].apply(list).to_dict()

    return menu


def parse_user_time(user_time):
    ''' format can be 7:00 PM, 7 PM, 7PM, 7:00PM, 7PM, 7 PM, 7PM, 7PM, 7'''
    formats = ["%I:%M %p", "%I %p", "%I %p", "%I:%M%p", "%I%p", "%I%p", "%I %p", "%I%p", "%I"]

    for fmt in formats:
        try:
            return datetime.strptime(user_time, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def is_time_within_window(delivery_time):
    """
    Checks if a given time is within a delivery window.

    Args:
        time (str): Time to check.
        window (str): Delivery window.

    Returns:
        bool: True if time is within the window, False otherwise.
    """
    cst_tz = pytz.timezone('America/Chicago')
    current_time = datetime.now(cst_tz)

    parsed_user_time = parse_user_time(delivery_time)
    user_time = cst_tz.localize(
        parsed_user_time.replace(
            year=current_time.year
            , month=current_time.month
            , day=current_time.day)
        )

    window_start = cst_tz.localize(datetime(current_time.year, current_time.month, current_time.day, 10, 0))  # Start at 10 AM
    window_end = cst_tz.localize(datetime(current_time.year, current_time.month, current_time.day, 19, 30))  # End at 7:30 PM

    return window_start <= user_time <= window_end

def make_reservation(reservation_date, name, phone_number, email_address, guests, reservation_type, address=None, delivery_time=None, reservation_time=None):
    """ function to make a reservation or book a table or dine-in """

    print('******** Inside make_reservation ********')

    if reservation_type.lower() == 'dine-in' and not reservation_time:
        return "For dine-in reservations, reservation_time is required."

    if reservation_type.lower() == 'delivery' and not address:
        return "For delivery reservations, address is required."

    if reservation_type.lower() == 'delivery' and not delivery_time:
        return "For delivery reservations, a delivery window is required."

    db = get_db()

    # Get a cursor
    cursor = db.cursor()

    cursor.execute('''
        INSERT INTO reservations (reservation_date, reservation_time, name, phone_number, email_address, guests, reservation_type, address, delivery_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (reservation_date
          , reservation_time
          , name
          , phone_number
          , email_address
          , guests
          , reservation_type
          , address
          , delivery_time)
    )

    reservation_number = cursor.lastrowid
    # Commit the changes
    db.commit()

    # Close the cursor
    cursor.close()
    return f"{reservation_type.capitalize()} confirmed for {name}. Reservation number: {reservation_number}."

def place_order(item, order_type, name, phone_number, email_address, address, delivery_time, customizations=None):
    """ function to place an order"""

    print('******** Inside place order ********')


    print(f"Ordering: {item}, Customizations: {customizations}, Order Type: {order_type}")

    if order_type.lower() == 'delivery' and not address:
        print('Error as address is not provided')
        return "Please provide the address for delivery."

    if order_type.lower() == 'delivery' and not delivery_time:
        print('Error as delivery time is not provided')
        return "Please select a delivery time."

    if not name or not phone_number:
        print('Error as name or phone number is not provided')
        return "Name and phone number are required for placing an order."

    if order_type.lower() == 'delivery' and not is_time_within_window(delivery_time):
        print('Error as delivery time is not within window')
        return "Delivery time must be 30 mins after the current time. First delivery is at 10AM and last at 7:30PM."

    message = make_reservation(
        reservation_date=datetime.now()
        , name=name
        , phone_number=phone_number
        , email_address=email_address
        , guests=0
        , reservation_type="Delivery"
        , address=address
        , delivery_time=delivery_time
    )

    return message

def cancel_reservation(reservation_number=None, phone_number=None):

    """ function to cancel a reservation"""

    print(f'******** Inside cancel_reservation {reservation_number} {phone_number} ********')

    if reservation_number:

        db = get_db()
        # Get a cursor
        cursor = db.cursor()

        reservation_number = int(reservation_number)
        filtered_reservations = cursor.execute('SELECT * FROM reservations WHERE reservation_number = ?', (reservation_number,)).fetchall()

        if filtered_reservations:
            cursor.execute('''DELETE FROM reservations WHERE reservation_number = ?''', (reservation_number,))
            db.commit()
            cursor.close()
            return f"Reservation number {reservation_number} has been cancelled"

        else:
            return f"Reservation number {reservation_number} not found."

    elif phone_number:

        db = get_db()
        # Get a cursor
        cursor = db.cursor()

        filtered_reservations = cursor.execute('SELECT * FROM reservations WHERE phone_number = ?', (phone_number,)).fetchall()

        if filtered_reservations:

            cursor.execute('''
                DELETE FROM reservations
                WHERE phone_number = ?''', (phone_number,))
            db.commit()
            cursor.close()
            return f"Reservations for phone number {phone_number} have been cancelled."
        else:
            return f"Reservation number {reservation_number} not found."
    else:
        return "Please provide either a reservation number or phone number to cancel."

# Other utility functions
def get_hours():
    """
    Retrieves the operating hours of the restaurant.

    Returns:
        str: Operating hours of the restaurant.
    """
    return "We are open from 10 AM to 10 PM every day."

def get_special_offers():
    """
    Retrieves special offers at the restaurant.

    Returns:
        str: Current special offers.
    """
    return "We have a 20% discount on all desserts this week!"

def get_location():
    """
    Retrieves the location of the restaurant.

    Returns:
        str: Location of the restaurant.
    """
    return "We are located at 123 Main Street, Anytown."

def contact_human():
    """ Get contact information for human assistance """
    return "You can reach us at (123) 456-7890 or email us at contact@restaurant.com."

function_descriptions = [
    {
        "name": "get_menu",
        "description": "Get the menu"
    },
    {
        "name": "place_order",
        "description": "Place an order for delivery",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "The item to order"},
                "email_address": {"type": "string", "description": "Email address for the order"},
                "name": {"type": "string", "description": "Name of the person placing the order"},
                "phone_number": {"type": "string", "description": "Phone number for the reservation"},
                "address": {"type": "string", "description": "Address for delivery"},
                "delivery_time": {"type": "string", "description": "Delivery time in PM or AM"},
                "customizations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of customizations for the item"
                },
                "order_type": {
                    "type": "string",
                    "enum": ["delivery"],
                    "description": "Type of order: delivery"
                }
            },
            "required": ["item", "order_type", "name", "phone_number", "email_address", "address", "delivery_time"]
        }
    },
    {
        "name": "make_reservation",
        "description": "Make a reservation or book a table for dine-in",
        "parameters": {
            "type": "object",
            "properties": {
                "reservation_date": {"type": "string", "description": "The date of the reservation"},
                "reservation_time": {"type": "string", "description": "The time of the reservation"},
                "name": {"type": "string", "description": "Name of the person under whom the reservation is made"},
                "phone_number": {"type": "string", "description": "Phone number for the reservation"},
                "email_address": {"type": "string", "description": "Email address for the reservation"},
                "guests": {"type": "integer", "description": "Number of guests"},
                "reservation_type": {
                    "type": "string",
                    "enum": ["dine-in"],
                    "description": "Type of reservation: dine-in"
                },
            },
            "required": ["reservation_date"
                         , "reservation_time"
                         , "name"
                         , "phone_number"
                         , "email_address"
                         , "guests", "reservation_type"]
        }
    },
    {
        "name": "cancel_reservation",
        "description": "Cancel a reservation or order",
        "parameters": {
            "type": "object",
            "properties": {
                "reservation_number": {"type": "integer", "description": "Reservation or order number to cancel"},
                "phone_number": {"type": "string", "description": "Phone number under which reservation or order was made"}
            }
        }
    },
    {"name": "get_hours", "description": "Get the operating hours"},
    {"name": "get_special_offers", "description": "Get the special offers"},
    {"name": "get_location", "description": "Get the location of the restaurant"},
    {"name": "contact_human", "description": "Get contact information for human assistance"}
]


# Function to interact with ChatGPT API
def chat_with_gpt(input_conversation):
    """
    Interacts with OpenAI's GPT model to handle user queries.

    Args:
        conversation (str): User query.

    Returns:
        str: Response generated by the chatbot.
    """


    chat_response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=input_conversation,
        functions=function_descriptions
        , function_call="auto"
    )

    response_message = dict(chat_response.choices[0].message)

    if response_message["content"] is None:
        response_message["content"] = ""

    return response_message

def initialize_conversation():
    '''
    Returns a list [{"role": "system", "content": system_message}]
    '''

    system_message = """
    You are the Masala Wok order bot. You are a helpful assistant and will help the customer
    - Look at the restaurant's menu
    - Place an order for delivery
    - Make a dine-in reservation
    - Cancel existing delivery order or dine-in reservation
    - Get the restaurant's operating hours
    - Get special offers
    - Get the location of the restaurant

    For each requests, you need to ask the user for all the required information.

    Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.

    Start with a short welcome message and encourage the user to share their requirements.
    """
    message = [{"role": "system", "content": system_message}]
    return message

# Example usage
if __name__ == "__main__":

    # # If you're using the default OpenAI API key, uncomment the following lines:
    openai.api_key = open("OpenAI_API_Key.txt", "r").read().strip()
    # os.environ['OPENAI_API_KEY'] = openai.api_key

    available_functions = {
        "get_menu": get_menu,
        "place_order": place_order,
        "make_reservation": make_reservation,
        "cancel_reservation": cancel_reservation,
        "get_hours": get_hours,
        "get_special_offers": get_special_offers,
        "get_location": get_location,
        "contact_human": contact_human
    }

    conversation = initialize_conversation()
    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "bye", "quit"]:
            print("RestaurantBot: Goodbye! We hope to see you again soon.")
            break

        conversation.append({"role": "user", "content": user_input})
        response = chat_with_gpt(conversation)

        print(f'......1.{response}')

        if response.get('function_call'):

            function_name = response['function_call'].name
            function_to_call = available_functions[function_name]
            params = json.loads(response['function_call'].arguments)
            function_response = function_to_call(**params)

            print(f'Assistant - Function name: {function_name}, function_to_call: {function_to_call}, "function_response: {function_response}')
            conversation.append({"role": "function",  "name": function_name, "content": json.dumps(function_response)})
            response = chat_with_gpt(conversation)
            print(f"RestaurantBot: 2.{response['content']}")
        else:
            print(f"RestaurantBot: 3.{response['content']}")

            conversation.append({"role": "assistant", "content": response['content']})

