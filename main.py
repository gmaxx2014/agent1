import requests
import json
import os
import gradio as gr
import random
from datetime import datetime

API_URL = "http://localhost:1234/v1/chat/completions"

photos = ["lingerie_photoshoot_backstage_selfie.png", 
          "lingerie_photoshoot.png", "selfie_nude_home.png", 
          "selfie_white_shirt.png", "selfie_work.png"]

# Read system prompt from file
def read_system_prompt(filename="system_prompt.txt", subfolder="resources/system_prompts"):
    try:
        file_path = os.path.join(subfolder, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Using default prompt.")
        return "no system prompt"
    except Exception as e:
        print(f"Error reading system prompt: {e}")
        return ""

# Read system prompts
system_prompt = read_system_prompt("system_prompt.txt")
system_character_prompt_lvl1 = read_system_prompt("system_character_prompt_lvl1.txt")
system_character_prompt_lvl2 = read_system_prompt("system_character_prompt_lvl2.txt")

current_level_prompt = system_character_prompt_lvl1
combined_prompt = f"{system_prompt}\n\n{current_level_prompt}"

# Chat history to preserve context
chat_history = [
    {"role": "system", "content": combined_prompt}
]

# Function to log conversation to console
def log_conversation(role, message, image_sent=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if role == "user":
        print(f"\n[{timestamp}] USER: {message}")
    elif role == "assistant":
        if image_sent:
            print(f"[{timestamp}] ASSISTANT: [PHOTO SENT] {message}")
        else:
            print(f"[{timestamp}] ASSISTANT: {message}")
    elif role == "system":
        print(f"[{timestamp}] SYSTEM: {message}")

# Log initial system prompt
log_conversation("system", f"System prompt loaded: {len(combined_prompt)} characters")

# Modified getImage function to return a random photo from the array
def getImage(query):
    print(f"[System] Getting photo for query: {query}")
    if photos:
        selected_photo = random.choice(photos)
        print(f"[System] Selected photo: {selected_photo}")
        return selected_photo
    else:
        return "no_photo_available.png"

def send_message(user_message, history):
    # Log user message
    log_conversation("user", user_message)
    
    # Append user message to chat history
    chat_history.append({"role": "user", "content": user_message})

    # Send request to LM Studio
    payload = {
        "model": "qwen3-8b",
        "messages": chat_history,
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Strip <think> if present
        if content.startswith("<think>"):
            content = content.split("</think>")[-1].strip()

        # Check for function call
        assistant_reply = content
        image_to_display = None
        image_sent = False
        
        try:
            parsed = json.loads(content)
            if parsed.get("function") == "getImage":
                query = parsed["arguments"]["query"]
                image_filename = getImage(query)
                assistant_reply = f"[Photo sent] {query}"
                image_to_display = "resources/images/" + image_filename
                image_sent = True
                print(f"[System] Image Path: {image_to_display}")
        except json.JSONDecodeError:
            pass

        # Log assistant response
        log_conversation("assistant", assistant_reply, image_sent)

        # Append assistant reply to chat history
        chat_history.append({"role": "assistant", "content": assistant_reply})

        # Update Gradio chat history
        if image_to_display:
            history.append([user_message, (image_to_display,)])
        else:
            history.append([user_message, assistant_reply])
        
        return "", history
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_conversation("system", f"Error occurred: {error_msg}")
        history.append([user_message, error_msg])
        return "", history

def clear_chat():
    global chat_history
    log_conversation("system", "Chat cleared by user")
    chat_history = [{"role": "system", "content": combined_prompt}]
    return []

def exit_app():
    log_conversation("system", "Application closed by user")
    print("Closing application...")
    os._exit(0)

# Load CSS
def load_css():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

css = load_css()

# Create the Gradio interface
with gr.Blocks(title="Chat with Babe", css=css, theme=gr.themes.Default()) as demo:
    gr.Markdown("# 💬 Chat with Babe", elem_classes=["mobile-friendly"])
    
    with gr.Column(elem_classes=["mobile-friendly"]):
        with gr.Column(elem_classes=["chat-container"]):
            chatbot = gr.Chatbot(
                label="",
                show_label=False,
                elem_classes=["chat-messages"]
            )
            
            with gr.Row(elem_classes=["chat-input"]):
                msg = gr.Textbox(
                    label="",
                    placeholder="Type your message...",
                    show_label=False,
                    scale=4,
                    container=False
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Chat")
                exit_btn = gr.Button("Exit", variant="stop")
    
    # Event handlers
    submit_event = msg.submit(
        send_message, 
        inputs=[msg, chatbot], 
        outputs=[msg, chatbot]
    )
    
    submit_btn.click(
        send_message, 
        inputs=[msg, chatbot], 
        outputs=[msg, chatbot]
    )
    
    clear_btn.click(clear_chat, outputs=[chatbot])
    exit_btn.click(exit_app)

if __name__ == "__main__":
    log_conversation("system", "Application started")
    demo.launch(share=True, inbrowser=True)