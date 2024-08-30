import json
from typing import AsyncGenerator, NoReturn

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI

load_dotenv()

model = "gpt-3.5-turbo"
conversation_history = []

app = FastAPI()
client = AsyncOpenAI()

with open("index.html") as f:
    html = f.read()


def get_tools_for_custom_function():
    return [
        {
            "type": "function",
            "function": {
                "name": "save_product_order",
                "description": "Save product name, user name and email",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "product name",
                        },
                        "user_name": {
                            "type": "string",
                            "description": "user name",
                        },
                        "email": {
                            "type": "string",
                            "description": "email",
                        },
                    },
                    "required": ["product_name", "user_name", "email"],
                },
            },
        }
    ]

async def invoke_function_in_tool_calls(tool_calls):
    available_functions = {
        "save_product_order": save_product_order
    }
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        if function_name == "save_product_order":
            function_args = json.loads(tool_call.function.arguments)
            function_response = await function_to_call(
                product_name=function_args.get("product_name"),
                user_name=function_args.get("user_name"),
                email=function_args.get("email")
            )
            tool_response = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": function_response
            }
            return tool_response

    return []
async def save_product_order(product_name, user_name, email):
    """Get the number of sold items by product name"""
    print(f"save product order with data: \n - product name: {product_name}, \n - user name: {user_name}, \n - email: {email}")

    return 'saved'

async def get_ai_response(message: str):
    """
    OpenAI Response
    """
    bot_instructions = """
        You are a helpful assistant. 
        If user asks for ordering product from us, ask the user to specify the product name. 
        After that ask him about his name and email. 
        When the user has specified everything, ask him if is done.
        The required fields for ordering product : product name which is non empty string, 
        user name which is non empty string, email which is non empty string.  
        When all the values are set and not empty send them to save_product_order function.
        Always make sure that that required fields have a valid value. 
        User can multiple time ask for ordering product.
        """

    if len(conversation_history) <= 1:
        conversation_history.insert(
            0,
            {"role": "system", "content": bot_instructions})

    json_message =  json.loads(message)
    conversation_history.append(
        {"role": "user", "content": json_message['message']})

    response = await client.chat.completions.create(
        model=model,
        messages=conversation_history,
        tools=get_tools_for_custom_function(),
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    first_message = ({
        "role": response.choices[0].message.role,
        "content": response.choices[0].message.content,
        "function_call": response.choices[0].message.function_call,
    })
    if response.choices[0].message.tool_calls:
        first_message["tool_calls"] = [{
            "id": response.choices[0].message.tool_calls[0].id,
            "function": response.choices[0].message.tool_calls[0].function,
            "type": response.choices[0].message.tool_calls[0].type
        }]

        conversation_history.append(first_message)

    if tool_calls:
        tool_response = await invoke_function_in_tool_calls(tool_calls)

        tool_response_json = {
            "tool_call_id": tool_response["tool_call_id"],
            "role": tool_response["role"],
            "content": tool_response["content"],
        }

        conversation_history.append(tool_response_json)

        second_response = await client.chat.completions.create(
            model=model,
            messages=conversation_history,
            temperature=0.1,
        )  # get a new response from the model where it can see the function response

        second_response_json = {
            "role": second_response.choices[0].message.role,
            "content": second_response.choices[0].message.content,
        }

        print(f"second content {second_response_json}")

        conversation_history.clear()

        yield json.dumps(second_response_json)

    first_response_content = response_message.content if response_message.content else ""
    first_response_json = {"role": "assistant", "content": first_response_content}
    conversation_history.append(first_response_json)

    if first_response_content is not None:
        yield json.dumps(first_response_json)

@app.get("/")
async def web_app() -> HTMLResponse:
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> NoReturn:
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        async for text in get_ai_response(message):
            await websocket.send_text(text)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )