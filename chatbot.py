# -*- coding: utf-8 -*-
"""ChatBot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1wZsuxo7bKlPC08Umyz9YzKZwz7lZ6tt-
"""

import openai
import pandas as pd
import json
import sqlite3
from difflib import get_close_matches

# # If you're using the default OpenAI API key, uncomment the following lines:
openai.api_key = open("OpenAI_API_Key.txt", "r").read().strip()
os.environ['OPENAI_API_KEY'] = openai.api_key

# Initialize SQLite database connection
conn = sqlite3.connect('restaurant.db')
c = conn.cursor()

# Create orders table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        customizations TEXT,
        order_type TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# In-memory reservations list
reservations = []

# Load menu from CSV
def get_menu():
    """
    Retrieves the menu items from a CSV file.

    Returns:
    dict: A dictionary where keys are categories and values are lists of items.
    """

    menu_df = pd.read_csv('menu.csv')

    menu = menu_df.groupby('category')['item'].apply(list).to_dict()

    return menu

# Handle order placement with customization and suggestion
def place_order(item, customizations, order_type):
    """
    Places an order with optional customizations.

    Args:
        item (str): The item to order.
        customizations (list): List of customizations for the item.
        order_type (str): Type of order, either 'delivery' or 'dine-in'.

    Returns:
        str: Confirmation message for the order.
    """
    menu = get_menu()
    all_items = [item for sublist in menu.values() for item in sublist]

    if item not in all_items:
        close_matches = get_close_matches(item, all_items, n=3)
        suggestion_message = f"'{item}' is not in our menu. Did you mean: {', '.join(close_matches)}?"
        return suggestion_message
    else:
        # Insert order into database
        c.execute('''
            INSERT INTO orders (item, customizations, order_type)
            VALUES (?, ?, ?)
        ''', (item, ', '.join(customizations) if customizations else None, order_type))
        conn.commit()

    return f"Order placed for {item} with customizations: {', '.join(customizations) if customizations else 'None'}."

# Handle reservation
def make_reservation(date, time, name, guests, reservation_type):
    """
    Makes a reservation for delivery or dine-in.

    Args:
        date (str): The date of the reservation.
        time (str): The time of the reservation.
        name (str): Name for the reservation.
        guests (int): Number of guests.
        reservation_type (str): Type of reservation, either 'delivery' or 'dine-in'.

    Returns:
        str: Confirmation message for the reservation.
    """
    reservations.append({
        'date': date,
        'time': time,
        'name': name,
        'guests': guests,
        'reservation_type': reservation_type
    })
    return f"{reservation_type.capitalize()} reservation confirmed for {name} on {date} at {time} for {guests} guests."

# Cancel reservation
def cancel_reservation(name, date, time):
    """
    Cancels a reservation.

    Args:
        name (str): Name of the reservation to cancel.
        date (str): Date of the reservation to cancel.
        time (str): Time of the reservation to cancel.

    Returns:
        str: Confirmation message for the cancellation.
    """
    global reservations
    reservations = [res for res in reservations if not (res['name'] == name and res['date'] == date and res['time'] == time)]
    return f"Reservation for {name} on {date} at {time} has been cancelled."

# Get all reservations
def get_reservations():
    """
    Retrieves all current reservations.

    Returns:
        str: Formatted string listing all reservations.
    """
    if not reservations:
        return "There are no reservations at the moment."

    reservation_list = "\n".join([f"{res['name']} - {res['date']} at {res['time']} for {res['guests']} guests ({res['reservation_type']})" for res in reservations])
    return f"Current reservations:\n{reservation_list}"

# Get all orders (for year-end auditing)
def get_all_orders():
    """
    Retrieves all orders from the database.

    Returns:
        list: List of tuples containing order details.
    """
    c.execute('''
        SELECT item, customizations, order_type, timestamp
        FROM orders
    ''')
    orders = c.fetchall()
    return orders

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

# Function definitions for ChatGPT
functions = [
    {"name": "get_menu", "description": "Get the menu"},
    {
        "name": "place_order",
        "description": "Place an order with customizations",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "The item to order"},
                "customizations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of customizations for the item"
                },
                "order_type": {
                    "type": "string",
                    "enum": ["delivery", "dine-in"],
                    "description": "Type of order: delivery or dine-in"
                }
            },
            "required": ["item", "order_type"]
        }
    },
    {
        "name": "make_reservation",
        "description": "Make a reservation",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "The date of the reservation"},
                "time": {"type": "string", "description": "The time of the reservation"},
                "name": {"type": "string", "description": "Name for the reservation"},
                "guests": {"type": "integer", "description": "Number of guests"},
                "reservation_type": {
                    "type": "string",
                    "enum": ["delivery", "dine-in"],
                    "description": "Type of reservation: delivery or dine-in"
                }
            },
            "required": ["date", "time", "name", "guests", "reservation_type"]
        }
    },
    {
        "name": "cancel_reservation",
        "description": "Cancel a reservation",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the reservation to cancel"},
                "date": {"type": "string", "description": "Date of the reservation to cancel"},
                "time": {"type": "string", "description": "Time of the reservation to cancel"}
            },
            "required": ["name", "date", "time"]
        }
    },
    {"name": "get_reservations", "description": "Get all reservations"},
    {
        "name": "get_all_orders",
        "description": "Get all orders for year-end auditing"
    },
    {"name": "get_hours", "description": "Get the operating hours"},
    {"name": "get_special_offers", "description": "Get the special offers"},
    {"name": "get_location", "description": "Get the location of the restaurant"}
]

# Function to interact with ChatGPT API
def chat_with_gpt(prompt, functions):
    """
    Interacts with OpenAI's GPT model to handle user queries.

    Args:
        prompt (str): User query.
        functions (list): List of supported functions.

    Returns:
        str: Response generated by the chatbot.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": "Welcome to the RestaurantBot! How can I assist you today?"}
        ],
        functions=functions
    )
    if response['choices'][0]['finish_reason'] == 'function_call':
        function_name = response['choices'][0]['message']['function_call']['name']
        arguments = json.loads(response['choices'][0]['message']['function_call']['arguments'])

        if function_name == 'get_menu':
            return get_menu()
        elif function_name == 'place_order':
            return place_order(arguments['item'], arguments.get('customizations', []), arguments['order_type'])
        elif function_name == 'make_reservation':
            return make_reservation(arguments['date'], arguments['time'], arguments['name'], arguments['guests'], arguments['reservation_type'])
        elif function_name == 'cancel_reservation':
            return cancel_reservation(arguments['name'], arguments['date'], arguments['time'])
        elif function_name == 'get_reservations':
            return get_reservations()
        elif function_name == 'get_all_orders':
            return get_all_orders()
        elif function_name == 'get_hours':
            return get_hours()
        elif function_name == 'get_special_offers':
            return get_special_offers()
        elif function_name == 'get_location':
            return get_location()
    else:
        return response['choices'][0]['message']['content']

# Example usage
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "bye", "quit"]:
            print("RestaurantBot: Goodbye! We hope to see you again soon.")
            break
        response = chat_with_gpt(user_input, functions)
        print(f"RestaurantBot: {response}")