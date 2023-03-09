import json
import os.path
import pathlib
import sys
import time
from signal import signal, SIGINT
from sys import exit


import requests

session_log = ""
session_start_time = ""
session_is_saved = False


def chat_gpt(text, api_key):
    url = "https://api.openai.com/v1/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": "text-davinci-003",
        "prompt": text,
        "max_tokens": 4000,
        "temperature": 1.0,
    }
    response = requests.post(url, headers=headers, json=data)

    return response.json()


def string_with_linebreak(input_string):
    current_line_len = 0
    result_str = ""
    max_line_length = 120
    for word in input_string.split():
        current_line_len += len(word) + 1
        if current_line_len > max_line_length:
            result_str += "\n" + word + " "
            current_line_len = len(word) + 1
        else:
            result_str += word + " "
    return result_str


def get_data_dir():
    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()
    data_dir: pathlib.Path
    if sys.platform == "win32":
        data_dir = home / "AppData/Roaming"
    elif sys.platform == "linux":
        data_dir = home / ".local/share"
    elif sys.platform == "darwin":
        data_dir = home / "Library/Application Support"
    else:
        data_dir = home

    data_dir = data_dir / "chatgptclient"

    try:
        data_dir.mkdir(parents=True)
    except FileExistsError:
        pass
    return str(data_dir)


def ask_question_and_log(question, api_key):
    global session_log

    dialogue = {}
    query_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    response = chat_gpt(question, api_key)
    response_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    dialogue["query_time"] = query_time
    dialogue["query"] = question
    dialogue["response_time"] = response_time
    dialogue["response"] = response

    complete_log_file = os.path.join(get_data_dir(), "chat_log_complete.json")
    simple_log_file = os.path.join(get_data_dir(), "chat_log.txt")

    with open(complete_log_file, "a") as fp:
        fp.write(json.dumps(dialogue, indent=2))
        fp.write("\n")

    simple_log = f"{query_time} query:\n" \
                 f"{string_with_linebreak(question)}\n" \
                 f"{response_time} response:\n" \
                 f"{string_with_linebreak(response['choices'][0]['text'].strip())}\n\n"

    with open(simple_log_file, "a") as fp:
        fp.write(simple_log)

    session_log += simple_log

    return response["choices"][0]["text"].strip()


def get_api_key():
    store = get_data_dir()
    api_key_file = os.path.join(store, "api_key")
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as fp:
            api_key = fp.read()
    else:
        try:
            api_key = input("Enter your API-key (https://beta.openai.com/account/api-keys):\n> ")
            with open(api_key_file, "w") as fp:
                fp.write(api_key)
        except EOFError:
            return ""
    return api_key


def main():
    api_key = None
    api_key = get_api_key()
    if not api_key:
        print("\nNo key submitted - exiting")
        return
    wait_text = "thinking..."

    next_question = True

    while next_question:
        try:
            question = input("Enter your Question:\n> ")
            print(wait_text, end="\r")
            answer = ask_question_and_log(question, api_key)
            spacing = (len(wait_text) - len(answer)) * " "
            print(f"{answer}{spacing}\n")
        except EOFError:
            next_question = False
            handler(None, None)
            return


def save_session():
    session_log_file = "chatgpt_log" + time.strftime("%Y-%m-%d_%H-%M-%S", session_start_time) + ".txt"
    session_log_file = os.path.join(os.getcwd(), session_log_file)
    with open(session_log_file, "a") as fp:
        fp.write(session_log)
    return session_log_file


def handler(signal_received, frame):
    global session_is_saved
    # print("", end="\n", flush=True)
    # yes_no = input("Save current session to local file? (y|n) ")
    # if yes_no == "y" or yes_no == "yes":
    if not session_is_saved and len(session_log) > 0:
        file_name = save_session()
        print("\nSaved session to", file_name)
        session_is_saved = True
    # else:
    #     print("bye")
    exit(0)


if __name__ == '__main__':
    signal(SIGINT, handler)
    session_start_time = time.localtime()
    main()
