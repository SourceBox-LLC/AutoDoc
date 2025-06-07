import tiktoken
import json
import os

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Return the number of tokens a plain string will use for the given model."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def format_number(num):
    """Format a number with commas as thousands separators"""
    return f"{num:,}"


if __name__ == "__main__":
    # Load repo_contents.json
    json_file = "repo_contents.json"
    
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found. Please generate it first.")
        exit(1)
    
    try:
        # Load the JSON data
        print(f"Loading {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            repo_data = json.load(f)
        
        # Calculate statistics
        num_files = len(repo_data)
        total_chars = sum(len(content) for content in repo_data.values())
        
        # Convert to a single string for token counting
        full_text = json.dumps(repo_data)
        
        # Count tokens for different models
        models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
        token_counts = {}
        
        print("\nCalculating token counts...")
        for model in models:
            token_counts[model] = count_tokens(full_text, model)
        
        # Print results
        print("\n=== Repository Content Statistics ===")
        print(f"Number of files: {format_number(num_files)}")
        print(f"Total characters: {format_number(total_chars)}")
        print("\n=== Token Count by Model ===")
        for model, count in token_counts.items():
            print(f"{model}: {format_number(count)} tokens")
        
        # Estimate costs (approximate as of 2025)
        print("\n=== Estimated Cost (USD) ===")
        costs = {
            "gpt-4o-mini": (8.0 / 1000000, 24.0 / 1000000),  # ($8/M input, $24/M output)
            "gpt-4o": (15.0 / 1000000, 60.0 / 1000000),      # ($15/M input, $60/M output)
            "gpt-4-turbo": (10.0 / 1000000, 30.0 / 1000000)  # ($10/M input, $30/M output)
        }
        
        for model, count in token_counts.items():
            if model in costs:
                input_cost_rate, output_cost_rate = costs[model]
                input_cost = count * input_cost_rate
                print(f"{model} input cost: ${input_cost:.4f}")
                
    except Exception as e:
        print(f"Error processing {json_file}: {e}")