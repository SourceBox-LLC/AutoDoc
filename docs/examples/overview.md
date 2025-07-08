```markdown
# Practical Code Examples for Project CADIA - CAD Generator

This document provides practical examples demonstrating how to use the main features of the Project CADIA repository. The examples will cover how to generate CAD files from text prompts using the provided API and the Streamlit application.

## Prerequisites

Before running the examples, ensure you have the required packages installed. Use the following command to install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Example 1: Running the Streamlit Application

To start the Streamlit application, which is the user interface for generating CAD files, navigate to the directory containing `app.py` and run:

```bash
streamlit run app.py
```

This will launch the application in your default web browser, allowing users to input descriptions for CAD designs.

### Example 2: Generating a CAD File from Command Line

You can generate a CAD file by directly calling the `generate_cad` function in `cad.py`. This example demonstrates how to use the command line for generating the CAD file.

1. Open your terminal.
2. Use the following command to specify a prompt and the desired output file name:

```bash
python cad.py "A simple chair design with four legs" -o "chair_design.step"
```

This command will generate a CAD file named `chair_design.step` based on the provided prompt.

### Example 3: Using the `generate_cad` Function Programmatically

You can also use the `generate_cad` function in a Python script. Below is an example of how to call this function programmatically:

```python
import os
from cad import generate_cad

def main():
    prompt = "Design a modern table with a glass top and wooden legs"
    output_file = "modern_table.step"

    try:
        # Set the API key in the environment
        os.environ["ZOO_API_TOKEN"] = "your_api_token_here"  # Replace with your actual API key

        # Generate the CAD file
        result_path = generate_cad(prompt, output_file)
        print(f"CAD file successfully generated and saved to: {result_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
```

In this example, replace `your_api_token_here` with your actual API token. This script prompts the API to generate a CAD file based on the specified design prompt.

### Example 