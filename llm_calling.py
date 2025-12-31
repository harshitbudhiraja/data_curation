from openai import OpenAI
import os
import tiktoken

def number_of_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(text))
    return num_tokens


def call_llm_local(user_prompt, system_prompt):
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

    resp = client.chat.completions.create(
        model="/Users/harshitbudhraja/Documents/research/dataset_curation/models/qwen_coder_3b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=200
    )
    return resp.choices[0].message.content


def call_llm_openrouter(user_prompt, system_prompt, model, max_tokens=1000, temperature=0.9, top_p=0.9):

    # print("Number of tokens in user prompt:",number_of_tokens(user_prompt))
    # print("Number of tokens in system prompt:",number_of_tokens(system_prompt))
    # print("Total number of tokens:",number_of_tokens(user_prompt) + number_of_tokens(system_prompt))

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    )   


    completion = client.chat.completions.create(
    extra_body={
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p

    },
    model=model,
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": system_prompt
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text", 
            "text": user_prompt
            }
        ]
        }
    ]
    )
    # print(completion.choices[0].message.content)
    if not completion.choices[0].message.content:
        print("Response is empty")
        with open('error_logs.json', 'a') as error_file:
            import json
            json.dump(completion.model_dump(), error_file, indent=2)
            error_file.write("\n")
    return completion.choices[0].message.content
