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

# Function to execute the bash script file
def execute_bash_script_file(file_path, quiet):
    if not quiet:
        subprocess.run(['sh', '-x', file_path])
    else:
        subprocess.run(['sh', file_path])

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Read the base prompt
    base_prompt_path = os.path.join(script_dir, 'baseprompt.txt')
    base_prompt = read_base_prompt(base_prompt_path)

    # Check for the -p and -q arguments
    print_only = '-p' in sys.argv
    quiet = '-q' in sys.argv
    if print_only:
        sys.argv.remove('-p')
    if quiet:
        sys.argv.remove('-q')

    # Get the command line input or read from stdin
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
    else:
        user_input = sys.stdin.read().strip()

    # Combine the base prompt with the user input
    full_prompt = f"{base_prompt}\n{user_input}"

    # Get the API key from the environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    # Get the summary of the input command
    summary_prompt = f"Give a unix-style file name, 15 characters or less without extension, prefer - over _ replacing spaces, summarizing this command:\n{user_input}"
    try:
        summary = get_chatgpt_response(api_key, summary_prompt)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Create the ai-summary.sh file
    command_file_path = os.path.join(os.getcwd(), f'ai-{summary}.sh')
    if not quiet:
        print(f"ai-{summary}.sh")
    with open(command_file_path, 'w') as command_file:
        command_file.write(f"#!/bin/bash\n# {user_input}\n\n")

    # Get the commands to execute
    try:
        commands = get_chatgpt_response(api_key, full_prompt)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Write the commands and print if not quiet
    with open(command_file_path, 'a') as command_file:
        command_file.write(commands)
        if not quiet:
            print(commands)

    # Print or execute the ai-summary.sh file based on the -p argument
    if print_only:
        with open(command_file_path, 'r') as command_file:
            print(command_file.read())
    else:
        execute_bash_script_file(command_file_path, quiet)

if __name__ == "__main__":
    main()
