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
def get_chatgpt_response(api_key, conversation):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4",
        "messages": conversation
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# Function to execute the bash script file and capture the output
def execute_bash_script_file(file_path, quiet):
    result = subprocess.run(['sh', file_path], capture_output=True, text=True)
    if not quiet:
        print(result.stdout)
    return result.stdout

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Read the base prompt
    base_prompt_path = os.path.join(script_dir, 'baseprompt.txt')
    base_prompt = read_base_prompt(base_prompt_path)

    # Check for the -q and -y arguments
    quiet = '-q' in sys.argv
    confirm = '-y' in sys.argv
    if quiet:
        sys.argv.remove('-q')
    if confirm:
        sys.argv.remove('-y')

    # Get the command line input or read from stdin
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
    else:
        user_input = sys.stdin.read().strip()

    # Initialize the conversation with the base prompt
    conversation = [{"role": "user", "content": base_prompt}]
    conversation.append({"role": "user", "content": user_input})

    # Get the API key from the environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    while True:
        # Get the commands to execute
        try:
            response = get_chatgpt_response(api_key, conversation)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Append the response to the conversation
        conversation.append({"role": "system", "content": response})

        # Parse the response and execute if needed
        if response.startswith("== EXECUTE ==") and response.endswith("== END =="):
            commands_to_execute = response[len("== EXECUTE =="):-len("== END ==")].strip()
            command_file_path = os.path.join(os.getcwd(), 'ai-temp.sh')
            with open(command_file_path, 'w') as command_file:
                command_file.write(f"#!/bin/bash\n{commands_to_execute}")

            print(commands_to_execute)

            # Ask for confirmation if -y argument is not provided
            if not confirm:
                user_confirmation = input("Execute? (y/n): ").strip().lower()
                if user_confirmation != 'y':
                    print("Execution aborted.")
                    sys.exit(0)

            # Execute the ai-temp.sh file and capture the output
            output = execute_bash_script_file(command_file_path, quiet)

            # Remove the ai-temp.sh file after execution
            os.remove(command_file_path)

            # Append the output to the conversation as a user message
            conversation.append({"role": "user", "content": output})
        elif response.startswith("== CHAT ==") and response.endswith("== END =="):
            chat_message = response[len("== CHAT =="):-len("== END ==")].strip()
            print(chat_message)
            user_response = input().strip()
            conversation.append({"role": "user", "content": user_response})
        elif response.startswith("== DONE =="):
            print("Chat session ended.")
            break
        else:
            print("No executable commands found in the response.")
            break

if __name__ == "__main__":
    main()
