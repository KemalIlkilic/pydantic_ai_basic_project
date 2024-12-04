from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import logfire

app = FastAPI()

logfire.configure(service_name="chatbot")
logfire.instrument_fastapi(app)


@app.get("/", response_class=HTMLResponse)
async def chatbot_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chatbot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f4f4f9;
            }
            #chatbox {
                width: 300px;
                height: 400px;
                border: 1px solid #ccc;
                overflow-y: scroll;
                padding: 10px;
                border-radius: 5px;
                background: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            #userInput {
                width: 200px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            #sendButton {
                height: 40px;
                padding: 0 15px;
                border: none;
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                margin-left: 10px;
            }
            #sendButton:hover {
                background-color: #0056b3;
            }
            .message {
                margin: 10px;
                padding: 5px;
                border-radius: 5px;
            }
            .user {
                background-color: #dfe9f3;
                text-align: left;
            }
            .bot {
                background-color: #e5e5e5;
                text-align: right;
            }
        </style>
    </head>
    <body>
        <div>
            <h1>Welcome to the Chatbot</h1>
            <div id="chatbox">
                <!-- Messages will be displayed here -->
            </div>
            <div>
                <input type="text" id="userInput" placeholder="Type a message..." />
                <button id="sendButton">Send</button>
            </div>
        </div>

        <script>
            const chatbox = document.getElementById('chatbox');
            const userInput = document.getElementById('userInput');
            const sendButton = document.getElementById('sendButton');

            const ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onopen = function(event) {
                console.log("Websocket is connected");
            }

            function appendMessage(sender, message) {
                const messageDiv = document.createElement('div');
                messageDiv.textContent = message;
                messageDiv.classList.add('message', sender);
                chatbox.appendChild(messageDiv);
                chatbox.scrollTop = chatbox.scrollHeight;
            }

            ws.onmessage = (event) => {
                console.log(event.data);
                const data = event.data;
                appendMessage('bot', data);
            };

            sendButton.addEventListener('click', () => {
                const userMessage = userInput.value.trim();
                if (!userMessage) return;

                appendMessage('user', userMessage);

                ws.send(userMessage);
                userInput.value = '';
            });

            ws.onclose = () => {
                appendMessage('bot', 'Connection closed.');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


model = OpenAIModel('gpt-4o', api_key="It is for your api key")
agent = Agent(model = model)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async for data in websocket.iter_text():
        #user_prompt: User input to start/continue the conversation.
        #message_history: History of the conversation so far.
        #agent.run returns: The result of the run.
        result = await agent.run(user_prompt=data, message_history=[])
        await websocket.send_text(result.data)
