import requests
import json
import os

API_URL = "http://localhost:1234/v1/chat/completions"

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

# Example getImage function
def getImage(query):
    # Replace this with your actual image generation logic
    print(f"[System] Generating image for query: {query}")
    # Simulate a URL return
    return f"images/{query.replace(' ', '_')}.png"

def send_message(user_message):
    # Append user message
    chat_history.append({"role": "user", "content": user_message})

    # Send request to LM Studio
    payload = {
        "model": "qwen3-8b",
        "messages": chat_history,
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Strip <think> if present
    if content.startswith("<think>"):
        content = content.split("</think>")[-1].strip()

    # Check for function call
    assistant_reply = content
    try:
        parsed = json.loads(content)
        if parsed.get("function") == "getImage":
            query = parsed["arguments"]["query"]
            image_url = getImage(query)
            assistant_reply = f"[Image generated] {image_url}"
    except json.JSONDecodeError:
        pass

    # Append assistant reply to chat history
    chat_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply

# Chat loop
print("Chat started. Type 'exit' to quit.")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break

    assistant_response = send_message(user_input)
    print(f"Babe: {assistant_response}")