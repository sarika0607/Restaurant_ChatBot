from flask import Flask, redirect, url_for, render_template, request
from functions import *

import openai
import json

openai.api_key = open("OpenAI_API_Key.txt", "r").read().strip()

app = Flask(__name__)

conversation_bot = []
conversation = initialize_conversation()
introduction = chat_with_gpt(conversation)
conversation_bot.append({'RestaurantBot': introduction})


@app.route("/")
def default_func():
    global conversation_bot, conversation
    return render_template("index.html", name_xyz = conversation_bot)

@app.route("/end_conv", methods = ['POST','GET'])
def end_conv():
    global conversation_bot, conversation
    conversation_bot = []
    conversation = initialize_conversation()
    introduction = chat_with_gpt(conversation)
    conversation_bot.append({'RestaurantBot':introduction})

    return redirect(url_for('default_func'))


@app.route("/invite", methods = ['POST'])
def invite():
    global conversation_bot, conversation

    user_input = request.form["user_input_message"]
    prompt = 'Remember your system message and that you are an intelligent restaurant bot. So, you only help with questions around the offering of this restaurant.'
    # moderation = moderation_check(user_input)
    # if moderation == 'Flagged':
    #     return redirect(url_for('end_conv'))


    # if top_3_laptops is None:
    conversation.append({"role": "user", "content": user_input + prompt})
    conversation_bot.append({'user':user_input})

    response = chat_with_gpt(conversation)

    if user_input.lower() in ["exit", "bye", "quit"]:
        print("bot: Goodbye! We hope to see you again soon.")
        conversation_bot.append({"bot": "Goodbye! We hope to see you again soon."})

        return redirect(url_for('default_func'))
    else:

        print(f"************bot: 1..{response}")
        if response.get('function_call'):
            # print(f"RestaurantBot: 3...{response.content}")

            chosen_function = eval(response['function_call'].name)
            params = json.loads(response['function_call'].arguments)
            print(f'************ {params} ************')
            output = chosen_function(**params)

            conversation.append({"role": "function",  "name": response['function_call'].name, "content": json.dumps(output)})
            response = chat_with_gpt(conversation)
            print(f"bot: 4..{response['content']}")
            conversation_bot.append({'bot':response['content']})

        else:
            print(f"bot: 5..{response['content']}")

            conversation.append({"role": "assistant", "content": response['content']})
            conversation_bot.append({'bot':response['content']})
            # response = chat_with_gpt(conversation)

    return redirect(url_for('default_func'))

if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0")




# -------



# -------------


# @app.route('/get', methods=['GET'])
# def get_bot_response():
#     user_input = request.args.get('msg')
#     conversation = []

#     if user_input:
#         conversation.append({"role": "user", "content": user_input})
#         response = chat_with_gpt(conversation)

#         if dict(response).get('function_call'):
#             chosen_function = eval(response.function_call.name)
#             params = json.loads(response.function_call.arguments)
#             output = chosen_function(**params)
#             conversation.append({"role": "function", "name": response.function_call.name, "content": json.dumps(output)})
#             response = chat_with_gpt(conversation)

#         conversation.append({"role": "assistant", "content": response.content})

#     bot_response = response.content
#     return jsonify(bot_response)

# if __name__ == "__main__":
#     app.run(debug=True)


# ---------------------


# @app.route("/")
# def index():
#     menu = get_menu()
#     return render_template('index.html', menu=menu)

# @app.route("/get", methods=['GET'])
# def get_bot_response():
#     user_text = request.args.get('msg')
#     conversation.append({"role": "user", "content": user_text})

#     # Call the chat_with_gpt function to get the bot's response
#     response = chat_with_gpt(conversation)

#     # Handle function calls if present in response
#     if response.get('function_call'):
#         chosen_function = eval(response['function_call']['name'])
#         params = json.loads(response['function_call']['arguments'])
#         output = chosen_function(**params)
#         conversation.append({"role": "function", "content": output})
#         response = chat_with_gpt(conversation)

#     conversation.append({"role": "bot", "content": response['content']})
#     bot_html = format_bot_response(response['content'])

#     return jsonify({'response': bot_html})

# @app.route("/invite", methods=["POST"])
# def invite():
#     user_input_message = request.form["user_input_message"]
#     conversation.append({"role": "user", "content": user_input_message})

#     return jsonify({'response': format_bot_response(user_input_message)})

# @app.route("/end
# continue
# ChatGPT
# Sure, here's the continuation and completion of the app.py script:

# python
# Copy code
# @app.route("/end_conv", methods=["POST"])
# def end_conversation():
#     global conversation
#     conversation = []  # Clear conversation history
#     return "Conversation ended."

# if __name__ == "__main__":
#     app.run(debug=True)

