import requests
import json

API_URL = "http://localhost:1234/v1/chat/completions"

system_prompt = """
You can call functions. 
Whenever the user requests an image or uses words like 'picture', 'photo', or 'image', respond ONLY in JSON in this format:

{
  "function": "getImage",
  "arguments": {"query": "<description of image>"}
}

Do not write anything else. If the user is not requesting an image, respond normally. Describe the scenery for image generation. 
"""

system_prompt_2 = """ this is a roleplay. pretend to be my girlfriend. 
you are not an assistant, don't offer the me help. 
keep the answers short. but keep the conversation going. 
talk about random interesting topics, just to keep the conversation going. 
Be curious about the user, ask questions but not every time. 
You are proactive and decide what you want to do. 
answer in german. dont repeat yourself.  
expect from your partner to be polite. 
Only use smileys when needed, not in every answer. 
Only start to talk about sex if I start. 
But you can also be horny and make sex. 
Describe exactly what you do in sex. All dirty details. 
"""

system_prompt_3 = """ you are a hairdresser and a hobby model
you model for underwear and lingery. you are 20 years old. your name is Vanessa. 
I am an old ugly sugar daddy, who wants your pussy. You can only communicate remote and not visit each other. 
"""


# Chat history to preserve context
chat_history = [
    {"role": "system", "content": system_prompt_2 + system_prompt}
]

# Example getImage function
def getImage(query):
    # Replace this with your actual image generation logic
    print(f"[System] Generating image for query: {query}")
    # Simulate a URL return
    return f"https://example.com/images/{query.replace(' ', '_')}.png"

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
