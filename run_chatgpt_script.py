import os
import sys
import requests
import subprocess
import platform

# Function to read the base prompt from a file
def read_base_prompt(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to get the response from OpenAI
def get_chatgpt_response(api_key, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# Function to execute the bash script returned by OpenAI
def execute_bash_script(script):
    if platform.system() == "Windows":
        process = subprocess.Popen(script, shell=True)
    else:
        process = subprocess.Popen(script, shell=True, executable='/bin/bash')
    process.communicate()

def main():
    # Read the base prompt
    base_prompt = read_base_prompt('baseprompt.txt')

    # Check for the -p argument
    print_only = '-p' in sys.argv
    if print_only:
        sys.argv.remove('-p')

    # Get the command line input
    user_input = ' '.join(sys.argv[1:])

    # Combine the base prompt with the user input
    full_prompt = f"{base_prompt}\n{user_input}"

    # Get the API key from the environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    # Get the response from OpenAI
    try:
        response = get_chatgpt_response(api_key, full_prompt)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Print or execute the returned bash script based on the -p argument
    if print_only:
        print(response)
    else:
        execute_bash_script(response)

if __name__ == "__main__":
    main()
