import asyncio
import argparse
import copy
from ai import get_ai_response, SYSTEM, parse_args # Assuming ai.py is in the same directory

async def run_test_prompt_with_params(user_prompt, system_prompt, specific_args, outfile):
    """Runs the chat function with a given prompt and specific parameters."""
    outfile.write("\n--- Testing with Parameters: ---\n")
    for key, value in vars(specific_args).items():
        outfile.write(f"{key}: {value}\n")
    outfile.write("---------------------------------\n")
    
    try:
        response = await get_ai_response(user_prompt, system_prompt, specific_args)
        outfile.write("\nAI Output:\n")
        if response:
            outfile.write(response + "\n")
        else:
            outfile.write("No response received or error occurred.\n")
        outfile.write("---------------------------------\n")
    except Exception as e:
        outfile.write(f"An error occurred: {e}\n")
        outfile.write("---------------------------------\n")

async def main():
    output_file_path = "ai_test_output.txt"
    user_prompt = "write a poem about a dog named buck."
    
    # Get default arguments from ai.py
    default_args = parse_args()

    # Define parameter sets to test
    # Each dictionary will override defaults for that specific test run
    param_variations = [
        {"temp": 0.2, "max_tokens": 100},  # Low temperature, short output
        {"temp": 0.7, "max_tokens": 250},  # Default temperature, medium output (control)
        {"temp": 1.0, "max_tokens": 250},  # High temperature, creative
        {"temp": 0.7, "top_p": 0.5, "max_tokens": 250}, # Using top_p
        {"temp": 0.7, "frequency_penalty": 0.5, "max_tokens": 250}, # With frequency penalty
        {"temp": 0.7, "presence_penalty": 0.5, "max_tokens": 250}, # With presence penalty
    ]

    with open(output_file_path, "w", encoding="utf-8") as outfile:
        outfile.write(f"Test run started for prompt: '{user_prompt}'\n")
        for variation in param_variations:
            # Create a fresh copy of default_args for each run
            current_args = copy.deepcopy(default_args)
            # Override defaults with current variation
            for key, value in variation.items():
                setattr(current_args, key, value)
            
            await run_test_prompt_with_params(user_prompt, SYSTEM, current_args, outfile)
        outfile.write("\nTest run complete.\n")
    print(f"Test output written to {output_file_path}")

if __name__ == "__main__":
    asyncio.run(main())
