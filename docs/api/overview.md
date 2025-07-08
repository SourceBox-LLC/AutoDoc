# Project CADIA - CAD Generator API Documentation

## Overview
Project CADIA is a web application designed to generate CAD files from natural language descriptions. The application leverages the capabilities of a text-to-CAD API, allowing users to create 3D models based on their input prompts.

## Table of Contents
1. [Modules](#modules)
   - [app.py](#apppy)
   - [cad.py](#cadpy)
2. [Functions](#functions)
   - [generate_cad](#generate_cad)
3. [Usage Examples](#usage-examples)

## Modules

### app.py
The `app.py` module serves as the main entry point for the Streamlit web application. It sets up the user interface, including page configurations, styling, and sidebar content.

#### Key Features
- **Page Configuration**: Sets the title, icon, layout, and sidebar state for the Streamlit app.
- **Custom CSS**: Provides styling for various components, including headers, buttons, and layout elements.
- **Sidebar**: Contains branding and navigation elements for the user.

### cad.py
The `cad.py` module is responsible for generating CAD files by interacting with the text-to-CAD API. It includes the `generate_cad` function, which handles the entire process of converting a text prompt to a CAD file.

## Functions

### `generate_cad(prompt: str, output_file: str = "output.step") -> str`
Generates a CAD file from a text prompt using the Zoo text-to-CAD API.

#### Parameters
- `prompt` (str): A text description of the design for the CAD file. This is the main input for generating the CAD model.
- `output_file` (str, optional): The file path where the generated CAD file will be saved. Defaults to `"output.step"`.

#### Returns
- (str): The file path of the generated CAD file.

#### Exceptions
- `ValueError`: Raised if the API key is not found in Streamlit secrets.
- `Exception`: Raised for various errors during the generation process, including API errors and timeout errors.

#### Usage Example
```python
from cad import generate_cad

try:
    result_file = generate_cad("A simple 3D cube design", "cube.step")
    print(f"CAD file successfully generated and saved to: {result_file}")
except Exception as e:
    print(f"An error occurred: {e}")
```

## Usage Examples

