import streamlit as st

from streamlit_ace import st_ace

def manual_edit_page(edit_input):
    """
    Renders the manual edit page with an Ace editor.
    This function uses `edit_input` as the initial content.

    Parameters:
        edit_input (str): The initial content for the Ace editor.

    Returns:
        str: The content from the Ace editor.
    """
    # -----------------------------
    # Sidebar: Editor Controls
    # -----------------------------
    st.sidebar.title("Editor Controls")

    # Select language for syntax highlighting
    editor_language = st.sidebar.selectbox(
        "Select Language",
        options=["python", "javascript", "html", "css", "sql"]
    )

    # Select a visual theme for the Ace editor
    editor_theme = st.sidebar.selectbox(
        "Select Theme",
        options=["monokai", "github", "dracula", "tomorrow", "twilight"]
    )

    # Adjust the font size used in the editor
    editor_font_size = st.sidebar.slider(
        "Font Size", min_value=10, max_value=30, value=14
    )

    # Adjust the height of the editor (in pixels)
    editor_height = st.sidebar.slider(
        "Editor Height (px)", min_value=200, max_value=1200, value=600
    )

    # Checkbox for enabling/disabling text wrapping
    enable_wrap = st.sidebar.checkbox("Enable Wrap", value=True)

    # Checkbox for live updates (auto updating the content as you type)
    enable_live_update = st.sidebar.checkbox("Live Update", value=True)

    # -----------------------------
    # Main Panel: Ace Editor and Content
    # -----------------------------
    # Create an Ace editor using the settings from the sidebar and the provided edit_input as the default.
    editor_content = st_ace(
        value=edit_input,
        language=editor_language,
        theme=editor_theme,
        font_size=editor_font_size,
        height=editor_height,
        wrap=enable_wrap,
        auto_update=enable_live_update,
    )

    # Display the current content of the editor below the editor
    st.subheader("Editor Content")
    st.code(editor_content, language=editor_language)
    
    return editor_content

if __name__ == "__main__":
    # Simulated input for testing
    edit_input = """
# Project Name

## Introduction

This project is a simple Python script that serves as a template for your software projects. The `template.py` file contains a basic "Hello World" print statement, which you can use as a starting point to build upon and customize according to your project's requirements.

## Prerequisites

Before you can use this project, you need to have Python (version 3.6 or later) installed.

## Installation

Clone the repository and run the script.

## Usage

Execute the script to see the "Hello World" message.

## License

[MIT License](LICENSE)
    """
    # Render the page using the simulated edit_input.
    manual_edit_page(edit_input)