from flask import Flask, redirect, url_for, render_template, request
from functions import *
import openai
import json

openai.api_key = open("OpenAI_API_Key.txt", "r").read().strip()

app = Flask(__name__)

conversation_bot = []
conversation = initialize_conversation()
introduction = chat_with_gpt(conversation)
conversation_bot.append({"bot":introduction['content']})


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
    conversation_bot.append({"bot":introduction['content']})

    return redirect(url_for('default_func'))


@app.route("/invite", methods = ['POST'])
def invite():
    global conversation_bot, conversation

    user_input = request.form["user_input_message"]
    prompt = 'Remember your system message and that you are an intelligent restaurant bot. So, you only help with questions around the offering of this restaurant.'

    conversation.append({"role": "user", "content": user_input + prompt})
    conversation_bot.append({'user': user_input})

    response = chat_with_gpt(conversation)

    if user_input.lower() in ["exit", "bye", "quit"]:
        print("bot: Goodbye! We hope to see you again soon.")
        conversation_bot.append({"bot": "Goodbye! We hope to see you again soon."})

        return redirect(url_for('default_func'))
    else:

        print(f"************bot: 1..{response}")
        if response.get('function_call'):
            # print(f"bot: 3...{response.content}")

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

    return redirect(url_for('default_func'))

if __name__ == '__main__':
    app.run(debug=True, host= "0.0.0.0")
