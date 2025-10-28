import requests
import json
import os
import gradio as gr
import random

API_URL = "http://localhost:1234/v1/chat/completions"

photos = ["lingerie_photoshoot_backstage_selfie.png", 
          "lingerie_photoshoot.png", "selfie_nude_home.png", 
          "selfie_white_shirt.png", "selfie_work.png"]

# Read system prompt from file
def read_system_prompt(filename="system_prompt.txt", subfolder="resources/system_prompts"):
    try:
        # Construct the full file path
        file_path = os.path.join(subfolder, filename)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Using default prompt.")
        return "no system prompt"
    except Exception as e:
        print(f"Error reading system prompt: {e}")
        return ""

# Read system prompt from file
system_prompt = read_system_prompt("system_prompt.txt")
system_character_prompt = read_system_prompt("system_character_prompt.txt")

combined_prompt = f"{system_prompt}\n\n{system_character_prompt}"

# Chat history to preserve context
chat_history = [
    {"role": "system", "content": combined_prompt}
]

# Modified getImage function to return a random photo from the array
def getImage(query):
    print(f"[System] Getting photo for query: {query}")
    # Select a random photo from the photos array
    if photos:
        selected_photo = random.choice(photos)
        print(f"[System] Selected photo: {selected_photo}")
        return selected_photo
    else:
        return "no_photo_available.png"

def send_message(user_message, history):
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
        
        try:
            parsed = json.loads(content)
            if parsed.get("function") == "getImage":
                query = parsed["arguments"]["query"]
                image_filename = getImage(query)
                assistant_reply = f"[Photo sent] {query}"
                image_to_display = "resources/images/" + image_filename
                print("Image Path: " + image_to_display)
        except json.JSONDecodeError:
            pass

        # Append assistant reply to chat history
        chat_history.append({"role": "assistant", "content": assistant_reply})

        # Update Gradio chat history
        if image_to_display:
            # If there's an image to display, add it to the chat
            history.append([user_message, (image_to_display,)])
        else:
            history.append([user_message, assistant_reply])
        
        return "", history
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append([user_message, error_msg])
        return "", history

def clear_chat():
    global chat_history
    # Reset chat history but keep system prompt
    chat_history = [{"role": "system", "content": combined_prompt}]
    return []

def exit_app():
    print("Closing application...")
    os._exit(0)

# Function to manually send a photo (for testing)
def send_photo():
    if photos:
        selected_photo = random.choice(photos)
        return selected_photo
    return None

def send_photo_message(history):
    selected_photo = send_photo()
    if selected_photo:
        # Add a system message indicating a photo was sent
        history.append(["", (selected_photo,)])
        return history
    return history

# Create the Gradio interface
with gr.Blocks(title="Chat Application") as demo:
    gr.Markdown("# Chat with Babe")
    
    chatbot = gr.Chatbot(
        label="Conversation",
        height=500,
        # Enable rendering of images in chat
        render_markdown=True
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Type your message",
            placeholder="Enter your message here...",
            scale=4,
            container=False
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)
    
    with gr.Row():
        clear_btn = gr.Button("Clear Chat", variant="secondary")
        send_photo_btn = gr.Button("Send Photo", variant="primary")
        exit_btn = gr.Button("Exit Application", variant="stop")
    
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
    
    clear_btn.click(
        clear_chat,
        outputs=[chatbot]
    )
    
    send_photo_btn.click(
        send_photo_message,
        inputs=[chatbot],
        outputs=[chatbot]
    )
    
    exit_btn.click(
        exit_app,
        inputs=None,
        outputs=None
    )

if __name__ == "__main__":
    demo.launch(share=False, inbrowser=True)