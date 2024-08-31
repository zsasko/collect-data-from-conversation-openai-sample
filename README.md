# How to collect data from chat conversation using OpenAI API

This project is sample application that demonstrates how we can collect data (product name, user name and email) from chat conversation using OpenAI API.

![](https://cdn-images-1.medium.com/max/800/1*-4OTiVjaQQjTkcFv_70OoQ.png)

It's a source code for the following article on the medium:

- https://medium.com/@zoransasko/how-to-collect-data-from-chat-conversation-using-openai-api-1849322735ac

## Open AI API key
Obtain your Open AI API key from the [Open AI web page](https://platform.openai.com/api-keys).

## Project setup
Create and activate a virtual environment by invoking the following command:
```
python -m venv venv
```
activate virtual environment by invoking:
```
source venv/bin/activate
```
or 
```
venv\Scripts\activate
```
(if your are using Windows) and install all required packages by invoking:
```
pip install -r requirements.txt
```

## Environment variables
Create your own `.env` file, using the `.env-example` as guidance and add OpenAI API key:
```
OPENAI_API_KEY = 'xxx'
```


## Running the project

For running the project, write:
```
python main.py
```
and you'll be able to see the application running in the following link:
```
http://0.0.0.0:8000
```
In order to start conversation you should write:
```
I want to order product
```
and when product name, user name and email are collected, in Python debug log you'll see them printed out.
