import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import subprocess
import shutil
import json
import asyncio
import argparse
from ai import get_ai_response, SYSTEM, parse_args as ai_parse_args, count_tokens # Renamed to avoid conflict if app.py has its own parse_args
from repo_tools import get_repo_file_tree, get_local_repo_contents, clone_github_repo  # Import functions from repo_tools.py

# Set page configuration
st.set_page_config(
    page_title="Lightning MD - Getting Started",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'sprint_model_params' not in st.session_state:
    st.session_state.sprint_model_params = {
        "model": "gpt-4o-mini",  # Using a faster model for Sprint mode
        "temp": 0.5,             # Lower temperature for more focused output
        "top_p": 0.85,           # Slightly more focused token selection
        "max_tokens": 2048,      # Reasonable length for documentation
        "pp": 0.0,               # Default presence penalty
        "fp": 0.0,               # Default frequency penalty
        "seed": None,            # No seed by default for variety
        "stop": None             # No custom stop sequences
    }

if 'model_params' not in st.session_state: # For Lightning Draft, initialize if needed
    st.session_state.model_params = st.session_state.sprint_model_params.copy() # Start with sprint defaults

if 'advanced_prompt_content' not in st.session_state:
    st.session_state.advanced_prompt_content = {}

if 'sprint_prompt_content' not in st.session_state:
    st.session_state.sprint_prompt_content = {}

if 'documentation_content' not in st.session_state:
    st.session_state.documentation_content = ""

if 'documentation_generated' not in st.session_state:
    st.session_state.documentation_generated = False

if 'documentation_config' not in st.session_state:
    st.session_state.documentation_config = {}

if 'repo_contents' not in st.session_state:
    st.session_state.repo_contents = {}

if 'repo_pulled' not in st.session_state:
    st.session_state.repo_pulled = False

if 'show_examine_repo' not in st.session_state:
    st.session_state.show_examine_repo = False

if 'lightning_sprint_active' not in st.session_state:
    st.session_state.lightning_sprint_active = False

if 'lightning_draft_active' not in st.session_state:
    st.session_state.lightning_draft_active = False

if 'show_review' not in st.session_state:
    st.session_state.show_review = False

if 'show_save_options' not in st.session_state:
    st.session_state.show_save_options = False

# Helper function to create an argparse.Namespace from a dictionary of parameters
def create_ai_args_namespace(params_dict):
    # Get default args from ai.py's parser
    default_args = ai_parse_args()
    
    # Override defaults with provided params
    for key, value in params_dict.items():
        if hasattr(default_args, key):
            setattr(default_args, key, value)
        # else: # Optional: handle unexpected params if necessary
            # print(f"Warning: Parameter '{key}' not found in AI default args.")
    return default_args

# Helper function to format the advanced prompt for Lightning Draft
def format_advanced_prompt(advanced_prompt_config):
    prompt_parts = []
    prompt_parts.append("Please generate comprehensive documentation for a software repository based on the following detailed requirements:")

    # Content
    content_config = advanced_prompt_config.get('content', {})
    prompt_parts.append("\n[Content Requirements]")
    prompt_parts.append(f"- Purpose of Documentation: {content_config.get('purpose', 'General understanding and usage')}")
    prompt_parts.append(f"- Desired Level of Detail (1-5, 5 is most detailed): {content_config.get('detail_level', 3)}")
    focus_areas = content_config.get('focus_areas', [])
    if focus_areas:
        prompt_parts.append(f"- Key Focus Areas: {', '.join(focus_areas)}")
    if content_config.get('custom_instructions'):
        prompt_parts.append(f"- Specific Custom Instructions: {content_config.get('custom_instructions')}")

    # Structure
    structure_config = advanced_prompt_config.get('structure', {})
    prompt_parts.append("\n[Structure Requirements]")
    prompt_parts.append(f"- Output Format: {structure_config.get('format', 'Markdown')}")
    sections = structure_config.get('sections', {})
    included_sections = [s_name for s_name, include in sections.items() if include]
    if included_sections:
        prompt_parts.append(f"- Mandatory Sections to Include: {', '.join(included_sections)}")
    else:
        prompt_parts.append("- Include standard documentation sections as appropriate.")

    # Style
    style_config = advanced_prompt_config.get('style', {})
    prompt_parts.append("\n[Style Requirements]")
    prompt_parts.append(f"- Writing Tone/Style: {style_config.get('tone', 'Clear, concise, and professional')}")
    prompt_parts.append(f"- Target Audience: {style_config.get('audience', 'Developers with intermediate experience')}")
    prompt_parts.append(f"- Preference for Code Examples: {style_config.get('code_examples', 'Include moderately detailed examples where relevant')}")

    prompt_parts.append("\nAdditionally, consider the overall structure of the repository to provide a coherent and useful document. The output must be valid Markdown.")
    return "\n".join(prompt_parts)


# Custom CSS for styling
st.markdown('''
<style>
    /* Reduce side margins to use more screen space */
    .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 95%;
    }
    
    /* Main panel styling */
    .main-panel-container {
        padding: 1rem;
        max-width: 100%;
    }
    
    /* Header styling */
    .main-panel-header {
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Improve spacing and alignment */
    .stButton button {
        border-radius: 5px;
    }
    
    /* Make sidebar buttons full width */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Adjust sidebar width */
    [data-testid="stSidebar"] {
        min-width: 250px;
        max-width: 300px;
    }
    .block-container {
        padding-top: 20px;
        padding-bottom: 20px;
        padding-left: 10px;
        padding-right: 10px;
    }
    
    /* Success messages styling */
    .element-container div[data-testid="stAlert"] {
        border-radius: 5px;
    }
</style>
''', unsafe_allow_html=True)


# Add this to your CSS
st.markdown('''
<style>
    /* Color scheme variables */
    :root {
        --primary: #4F46E5;
        --primary-hover: #4338CA;
        --secondary: #06B6D4;
        --light-bg: #F9FAFB;
        --dark-text: #1F2937;
        --light-text: #6B7280;
        --success: #10B981;
        --warning: #F59E0B;
        --error: #EF4444;
    }
    
    /* Apply colors to elements */
    .stButton button {
        background-color: var(--primary);
        color: white;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: var(--primary-hover);
    }
    
    /* Step buttons styling */
    [data-testid="stSidebar"] .stButton button:nth-of-type(1) {
        background-color: var(--primary);
    }
    [data-testid="stSidebar"] .stButton button:nth-of-type(2) {
        background-color: var(--secondary);
    }
</style>
''', unsafe_allow_html=True)

# Add this to your CSS
st.markdown('''
<style>
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .main-panel-container {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    .stButton button {
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
    }
</style>
''', unsafe_allow_html=True)

# Add CSS for lightning animation
st.markdown('''
<style>
    /* Lightning animation */
    @keyframes lightning {
        0% {
            opacity: 0;
        }
        25% {
            opacity: 1;
        }
        30% {
            opacity: 0.6;
        }
        35% {
            opacity: 1;
        }
        40% {
            opacity: 0;
        }
        45% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
        55% {
            opacity: 0;
        }
        60% {
            opacity: 0.4;
        }
        65% {
            opacity: 0;
        }
        100% {
            opacity: 0;
        }
    }
    
    .lightning-bolt {
        font-size: 80px;
        color: var(--primary);
        animation: lightning 3s infinite;
        margin-bottom: 20px;
    }
    
    .lightning-bolt:nth-child(2) {
        animation-delay: 0.5s;
        color: var(--secondary);
    }
    
    .lightning-bolt:nth-child(3) {
        animation-delay: 1s;
        color: var(--success);
    }
    
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 50px 20px;
        height: 400px;
    }
    
    .welcome-text {
        color: var(--dark-text);
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
</style>
''', unsafe_allow_html=True)


# Replace your current header with a more attractive hero section
st.markdown('''
<div style="text-align: center; padding: 30px 0; background: linear-gradient(90deg, #4F46E5 0%, #06B6D4 100%); border-radius: 10px; margin-bottom: 30px;">
    <h1 style="color: white; font-size: 48px; margin-bottom: 10px;">⚡ Lightning MD</h1>
    <p style="color: white; font-size: 20px; max-width: 600px; margin: 0 auto;">
        Generate beautiful documentation for your repositories with AI-powered speed and accuracy.
    </p>
</div>
''', unsafe_allow_html=True)


st.divider()

# Create a visually appealing workflow steps indicator
st.sidebar.markdown("<h2 style='margin-bottom:15px;'>Workflow Steps</h2>", unsafe_allow_html=True)

# Determine the active step based on session state
active_step = 1
if 'show_save_options' in st.session_state and st.session_state.show_save_options:
    active_step = 5
elif 'show_review' in st.session_state and st.session_state.show_review:
    active_step = 4
elif 'documentation_generated' in st.session_state and st.session_state.documentation_generated:
    active_step = 4
elif 'lightning_sprint_active' in st.session_state and st.session_state.lightning_sprint_active or 'lightning_draft_active' in st.session_state and st.session_state.lightning_draft_active:
    active_step = 3
elif 'show_step3' in st.session_state and st.session_state.show_step3:
    active_step = 3
elif 'show_repo_contents' in st.session_state and st.session_state.show_repo_contents:
    active_step = 2
elif 'repo_pulled' in st.session_state and st.session_state.repo_pulled:
    active_step = 2

# Define steps
steps = [
    {"number": 1, "name": "Pull Repository"},
    {"number": 2, "name": "Examine Repository"},
    {"number": 3, "name": "Generate Documentation"},
    {"number": 4, "name": "Review Documentation"},
    {"number": 5, "name": "Save Documentation"}
]

# Render the steps with appropriate styling
for step in steps:
    if step["number"] < active_step:
        # Completed step
        st.sidebar.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:12px;">
            <div style="background-color:var(--success); color:white; width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:10px; font-weight:bold;">✓</div>
            <div style="color:var(--success); font-weight:500;">{step["name"]}</div>
        </div>
        """, unsafe_allow_html=True)
    elif step["number"] == active_step:
        # Current active step
        st.sidebar.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:12px;">
            <div style="background-color:var(--primary); color:white; width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:10px; font-weight:bold;">{step["number"]}</div>
            <div style="color:var(--primary); font-weight:600;">{step["name"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Inactive step
        st.sidebar.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:12px; opacity:0.6;">
            <div style="background-color:var(--light-text); color:white; width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; margin-right:10px; font-weight:bold;">{step["number"]}</div>
            <div style="color:var(--light-text);">{step["name"]}</div>
        </div>
        """, unsafe_allow_html=True)


# Determine the current active step
def get_current_step():
    if not st.session_state.repo_pulled:
        return 1  # Step 1: Pull Repository
    elif not st.session_state.show_step3:
        return 2  # Step 2: Examine Repository
    elif not st.session_state.documentation_generated:
        return 3  # Step 3: Generate Documentation
    elif not (st.session_state.show_review or st.session_state.show_save_options):
        return 3  # Still in Step 3
    elif not st.session_state.show_save_options:
        return 4  # Step 4: Review Documentation
    else:
        return 5  # Step 5: Save Documentation

current_step = get_current_step()

# Only show reversion options if we're past step 1
if current_step > 1:
    st.sidebar.markdown("### Revert to Previous Step")
    
    # Create options for steps the user can go back to
    step_options = []
    step_labels = ["1: Pull Repository", "2: Examine Repository", "3: Generate Documentation", "4: Review Documentation"]
    
    # Only include steps that are before the current step
    for i in range(current_step - 1):
        step_options.append(step_labels[i])
    
    if step_options:
        revert_option = st.sidebar.selectbox(
            "Select a step to revert to:",
            options=step_options
        )
        
        if st.sidebar.button("Revert to Selected Step"):
            # Extract the step number from the selected option
            selected_step = int(revert_option.split(":")[0])
            
            # Reset state based on the selected step
            if selected_step <= 1:
                # Reset to Step 1 (Pull Repository)
                st.session_state.repo_pulled = False
                st.session_state.show_step3 = False
                st.session_state.documentation_generated = False
                st.session_state.documentation_content = ""
                st.session_state.show_review = False
                st.session_state.show_save_options = False
                st.session_state.lightning_sprint_active = False
                st.session_state.lightning_draft_active = False
                if 'repo_contents' in st.session_state:
                    del st.session_state.repo_contents
                
            elif selected_step <= 2:
                # Reset to Step 2 (Examine Repository)
                st.session_state.show_step3 = False
                st.session_state.documentation_generated = False
                st.session_state.documentation_content = ""
                st.session_state.show_review = False
                st.session_state.show_save_options = False
                st.session_state.lightning_sprint_active = False
                st.session_state.lightning_draft_active = False
                
            elif selected_step <= 3:
                # Reset to Step 3 (Generate Documentation)
                st.session_state.documentation_generated = False
                st.session_state.documentation_content = ""
                st.session_state.show_review = False
                st.session_state.show_save_options = False
                st.session_state.lightning_sprint_active = False
                st.session_state.lightning_draft_active = False
            
            # Force UI refresh
            st.rerun()



st.sidebar.markdown("<hr style='margin: 15px 0 20px 0;'>", unsafe_allow_html=True)

# Add this to your CSS
st.markdown('''
<style>
    /* Micro-interactions */
    .stCheckbox:hover, .stRadio:hover {
        transform: scale(1.02);
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"] {
        border: 2px dashed #E5E7EB;
        border-radius: 10px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #4F46E5;
    }
</style>
''', unsafe_allow_html=True)



# Main panel with styled container - header will appear in each view

# Initialize session state for tracking app state
if 'repo_pulled' not in st.session_state:
    st.session_state.repo_pulled = False
    
if 'show_repo_contents' not in st.session_state:
    st.session_state.show_repo_contents = False
    
if 'show_step3' not in st.session_state:
    st.session_state.show_step3 = False
    
if 'lightning_sprint_active' not in st.session_state:
    st.session_state.lightning_sprint_active = False
    
if 'lightning_draft_active' not in st.session_state:
    st.session_state.lightning_draft_active = False
    
# Session state for storing and reviewing documentation
if 'documentation_generated' not in st.session_state:
    st.session_state.documentation_generated = False
    
if 'documentation_content' not in st.session_state:
    st.session_state.documentation_content = ""
    
if 'show_review' not in st.session_state:
    st.session_state.show_review = False
    
if 'show_save_options' not in st.session_state:
    st.session_state.show_save_options = False

# Callback functions to update session state
def on_pull_repo():
    # Get the repository URL from the text input's current value in session state
    github_url = st.session_state.repo_url
    
    # Only proceed if URL is provided
    if not github_url or github_url.strip() == "":
        st.sidebar.error("Please enter a valid GitHub repository URL")
        return
    
    try:
        # Use the clone_github_repo function from repo_tools.py to actually clone the repository
        with st.sidebar.status("Cloning repository...") as status:
            # Check if repository directory exists
            repo_dir = "repo"
            if os.path.exists(repo_dir):
                status.update(label=f"Preparing to replace existing repository...")
                # Handling is done inside clone_github_repo function, just informing the user
            
            # Clone the repository
            status.update(label=f"Cloning {github_url}...")
            clone_github_repo(github_url)
            status.update(label="Repository cloned successfully!", state="complete", expanded=False)
        
        # After successful clone, update the session state
        st.session_state.repo_pulled = True
        
        # Reset any session state related to repository content
        if 'repo_contents' in st.session_state:
            del st.session_state.repo_contents
            
    except Exception as e:
        st.sidebar.error(f"Error cloning repository: {str(e)}")
        st.session_state.repo_pulled = False
    
def on_examine_repo():
    st.session_state.show_repo_contents = True
    st.session_state.show_step3 = True
    
    # Store repo contents in session state
    repo_path = "repo"
    if os.path.exists(repo_path) and os.path.isdir(repo_path):
        st.session_state.repo_contents = get_local_repo_contents(repo_path)
    
def on_lightning_sprint():
    st.session_state.lightning_sprint_active = True
    # When Lightning Sprint is activated, deactivate other modes
    st.session_state.show_repo_contents = False
    st.session_state.lightning_draft_active = False
    
def on_lightning_draft():
    st.session_state.lightning_draft_active = True
    # When Lightning Draft is activated, deactivate other modes
    st.session_state.show_repo_contents = False
    st.session_state.lightning_sprint_active = False
    st.session_state.show_review = False
    
def on_review_documentation():
    # When Review Documentation is activated, deactivate other modes
    st.session_state.show_review = True
    st.session_state.lightning_draft_active = False
    st.session_state.lightning_sprint_active = False
    st.session_state.show_repo_contents = False
    st.session_state.show_save_options = False
    
def on_save_documentation():
    # When Save Documentation is activated, deactivate other modes
    st.session_state.show_save_options = True
    st.session_state.show_review = False
    st.session_state.lightning_draft_active = False
    st.session_state.lightning_sprint_active = False
    st.session_state.show_repo_contents = False

# Check if documentation has been generated
docs_generated = st.session_state.get('documentation_generated', False)

# Add a sidebar
# Use different styling for headers based on whether documentation is generated
if docs_generated:
    st.sidebar.markdown("<h3 style='color: #AAAAAA;'>Step 1.) Pull Repository</h3>", unsafe_allow_html=True)
else:
    st.sidebar.header("Step 1.) Pull Repository")

# Store repo URL in session state so it can be accessed by the callback function
if 'repo_url' not in st.session_state:
    st.session_state.repo_url = "https://github.com/username/repository.git"

# Disable Step 1 if documentation has been generated
if docs_generated:
    st.sidebar.text_input("Repository URL", key="repo_url", value=st.session_state.repo_url, disabled=True)
    st.sidebar.button("Pull Repository", disabled=True)
else:
    # Use the widget without a default value to avoid the soft warning
    repo_url = st.sidebar.text_input("Repository URL", key="repo_url")
    
    # Pull Repository button with callback
    pull_repo = st.sidebar.button("Pull Repository", on_click=on_pull_repo)

# Show status message if repo was pulled
if st.session_state.repo_pulled:
    st.sidebar.success("Repository Pulled!")
    
    # Step 2 options appear after repo is pulled
    st.sidebar.divider()
    
    # Use different styling for headers based on whether documentation is generated
    if docs_generated:
        st.sidebar.markdown("<h3 style='color: #AAAAAA;'>Step 2.) Examine Repository</h3>", unsafe_allow_html=True)
    else:
        st.sidebar.header("Step 2.) Examine Repository")
    
    # Disable Step 2 if documentation has been generated
    if docs_generated:
        st.sidebar.button("Examine Repository", disabled=True)
    else:
        examine_repo = st.sidebar.button("Examine Repository", on_click=on_examine_repo)
    
    # Step 3 appears after repository is examined
    if st.session_state.show_step3:
        st.sidebar.divider()
        
        # Check if user is in Step 4 (reviewing or saving) to determine if Step 3 should be locked
        in_step4 = st.session_state.get('show_review', False) or st.session_state.get('show_save_options', False)
        
        # Gray out Step 3 header if in Step 4
        if in_step4:
            st.sidebar.markdown("<h3 style='color: #AAAAAA;'>Step 3.) Generate Documentation</h3>", unsafe_allow_html=True)
        else:
            st.sidebar.header("Step 3.) Generate Documentation")
            
        # Disable Step 3 buttons if in Step 4
        if in_step4:
            st.sidebar.button("Lightning Sprint", disabled=True)
            st.sidebar.button("Lightning Draft", disabled=True)
        else:
            st.sidebar.button("Lightning Sprint", on_click=on_lightning_sprint)
            st.sidebar.button("Lightning Draft", on_click=on_lightning_draft)
        
        # Step 4 appears after documentation is generated
        if st.session_state.documentation_generated:
            st.sidebar.divider()
            st.sidebar.header("Step 4.) Review Documentation")
            st.sidebar.button("Review", on_click=on_review_documentation)
            
            # Step 5 appears after documentation is reviewed
            if st.session_state.show_review or st.session_state.show_save_options:
                st.sidebar.divider()
                st.sidebar.header("Step 5.) Save Documentation")
                st.sidebar.button("Save Options", on_click=on_save_documentation)

# Function to display directory contents
def display_directory_contents(path, indent=0):
    """Recursively display directory contents in a tree-like structure"""
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in sorted(files):
            file_path = os.path.join(path, file)
            is_dir = os.path.isdir(file_path)
            icon = "📁 " if is_dir else "📄 "
            st.write(f"{' ' * indent}{icon}{file}")
            
            # Recursively display contents of subdirectories (limit depth to avoid too much nesting)
            if is_dir and indent < 12:  # Limit nesting level
                display_directory_contents(file_path, indent + 4)

# Add a styled container for main content
st.markdown('<div class="main-panel-container">', unsafe_allow_html=True)
repo_container = st.container()
st.markdown('</div>', unsafe_allow_html=True)

# Check which content to display in the main panel
if st.session_state.show_save_options:
    # Display documentation save options screen
    with repo_container:
        # Use markdown with HTML for centered headers
        st.markdown("<h1 style='text-align: center; color: grey;'>💾 Save Documentation</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Choose how to save your documentation</h3>", unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.documentation_generated and st.session_state.documentation_content:
            # Create a container for file format options
            st.write("### 1. Select Format")
            format_options = st.radio(
                "File Format",
                ["Markdown (.md)", "HTML (.html)", "PDF (.pdf)", "Word Document (.docx)"],
                horizontal=True
            )
            
            # Create a container for export options
            st.write("### 2. Export Options")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Quick Actions**")
                
                # Direct download button
                st.download_button(
                    label="Download Documentation",
                    data=st.session_state.documentation_content,
                    file_name="documentation.md",
                    mime="text/markdown",
                    help="Download documentation in the selected format directly to your computer"
                )
                
                # Copy to clipboard button
                if st.button("Copy to Clipboard", help="Copy the entire documentation to your clipboard"):
                    st.success("Documentation copied to clipboard! (This would work in the complete app)")
                    
                # Save to GitHub Gist
                if st.button("Save as GitHub Gist", help="Create a GitHub Gist from your documentation"):
                    st.info("This would create a GitHub Gist in the complete app")
                    # This would require GitHub API integration in a complete app
            
            with col2:
                st.write("**Advanced Options**")
                
                # File name customization
                custom_filename = st.text_input(
                    "Filename", 
                    "documentation", 
                    help="Enter a custom filename (without extension)"
                )
                
                # Include metadata checkbox
                include_metadata = st.checkbox(
                    "Include Generation Metadata", 
                    value=True,
                    help="Add metadata such as generation date and repository info"
                )
                
                # Include table of contents
                include_toc = st.checkbox(
                    "Include Table of Contents", 
                    value=True,
                    help="Automatically generate a table of contents"
                )
                
                # Export with settings button
                if st.button("Export with Settings"):
                    # This would apply the selected options in a complete app
                    filename = f"{custom_filename}.md" if format_options == "Markdown (.md)" else f"{custom_filename}.{format_options.split('.')[-1].strip(')')}" 
                    st.success(f"Documentation exported as {filename} with your selected settings!")
            
            # Integration options
            st.write("### 3. Integration Options")
            st.info("In the complete app, you would have options to save to:")
            
            integration_cols = st.columns(4)
            with integration_cols[0]:
                st.button("📡 SharePoint", disabled=True)
            with integration_cols[1]:
                st.button("📝 Notion", disabled=True)
            with integration_cols[2]:
                st.button("📊 Confluence", disabled=True)
            with integration_cols[3]:
                st.button("📋 Google Docs", disabled=True)
                
            # Documentation preview
            with st.expander("Preview Documentation"):
                st.markdown(st.session_state.documentation_content)
                
        else:
            st.warning("No documentation has been generated yet. Please generate documentation in Step 3 first.")
            if st.button("Go to Step 3"):
                # Reset to show Step 3
                st.session_state.show_save_options = False
                st.session_state.show_step3 = True
                
elif st.session_state.show_review:
    # Display documentation review screen
    with repo_container:
        st.markdown("<h1 style='text-align: center; color: grey;'>📋 Documentation Review</h1>", unsafe_allow_html=True)

        
        if st.session_state.documentation_generated and st.session_state.documentation_content:
            # Create tabs for different views
            preview_tab, raw_tab = st.tabs(["Preview", "Raw Markdown"])
            
            with preview_tab:
                st.markdown(st.session_state.documentation_content)
                
                # Add feedback options for parameter tuning
                st.divider()
                st.subheader("Feedback")
                st.write("How would you rate this documentation?")
                rating = st.slider("Rating", 1, 5, 4)
                
                # Add specific feedback categories that can be used for parameter tuning
                quality_cols = st.columns(3)
                with quality_cols[0]:
                    clarity = st.select_slider(
                        "Clarity",
                        options=["Poor", "Fair", "Good", "Excellent"],
                        value="Good"
                    )
                with quality_cols[1]:
                    completeness = st.select_slider(
                        "Completeness",
                        options=["Poor", "Fair", "Good", "Excellent"],
                        value="Good"
                    )
                with quality_cols[2]:
                    technical_accuracy = st.select_slider(
                        "Technical Accuracy",
                        options=["Poor", "Fair", "Good", "Excellent"],
                        value="Good"
                    )
                    
                feedback_text = st.text_area("Comments or suggestions for improvement:")
                
                if st.button("Submit Feedback"):
                    # Create feedback data structure
                    feedback_data = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "rating": rating,
                        "clarity": clarity,
                        "completeness": completeness,
                        "technical_accuracy": technical_accuracy,
                        "comments": feedback_text,
                        "model_params": st.session_state.get("model_params", {}),
                        "prompt_content": st.session_state.get("advanced_prompt_content", {})
                    }
                    
                    # Create feedback directory if it doesn't exist
                    os.makedirs("feedback", exist_ok=True)
                    
                    # Save feedback to a JSON file
                    feedback_file = f"feedback/feedback_{int(time.time())}.json"
                    with open(feedback_file, "w") as f:
                        json.dump(feedback_data, f, indent=4)
                    
                    st.success(f"Feedback saved to {feedback_file}! This will be used to tune future parameters.")
                    
                    # Display the saved feedback
                    with st.expander("View saved feedback data"):
                        st.json(feedback_data)
            
            with raw_tab:
                st.code(st.session_state.documentation_content, language="markdown")
                
                if st.button("Copy to Clipboard"):
                    st.success("Markdown copied to clipboard! (This would work in the complete app)")
                
                # Download button
                st.download_button(
                    label="Download Markdown",
                    data=st.session_state.documentation_content,
                    file_name="documentation.md",
                    mime="text/markdown"
                )
            
            # Show next step button
            st.divider()
            st.write("Ready to proceed to the next step?")
            if st.button("Proceed to Step 5: Save Documentation"):
                st.info("Step 5 would be implemented in the complete app.")
                
        else:
            st.warning("No documentation has been generated yet. Please generate documentation in Step 3 first.")
            if st.button("Go to Step 3"):
                # Reset to show Step 3
                st.session_state.show_review = False
                st.session_state.show_step3 = True
                
elif st.session_state.lightning_draft_active:
    # Display advanced options for Lightning Draft mode
    with repo_container:
        # Use markdown with HTML for centered headers
        st.markdown("<h1 style='text-align: center; color: grey;'>📝 Lightning Draft</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Advanced Documentation Generation</h3>", unsafe_allow_html=True)
        st.divider()
        
        st.write("Configure your documentation generation options:")
        
        # Create tabs for different configuration sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Content", "Structure", "Style", "Model Settings", "Import Config"])
        
        with tab1:
            st.subheader("Content Options")
            
            # Primary documentation purpose
            doc_purpose = st.selectbox(
                "Documentation Purpose",
                ["API Reference", "User Guide", "Developer Guide", "System Architecture", "Custom"],
                index=0
            )
            
            # Depth and detail level
            detail_level = st.slider(
                "Detail Level",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = High-level overview, 5 = Detailed implementation"
            )
            
            # Content focus areas (multiselect)
            focus_areas = st.multiselect(
                "Focus Areas",
                ["Code Structure", "Function Documentation", "Usage Examples", 
                 "Installation Instructions", "Dependencies", "Testing", "Performance"],
                default=["Code Structure", "Function Documentation"]
            )
            
            # Custom prompt/instructions
            custom_instructions = st.text_area(
                "Additional Instructions",
                """Please include relevant code examples and usage patterns.""",
                height=100
            )
        
        with tab2:
            st.subheader("Structure Options")
            
            # Documentation format
            doc_format = st.radio(
                "Output Format",
                ["Markdown", "HTML", "ReStructuredText"],
                horizontal=True
            )
            
            # Table of contents
            include_toc = st.checkbox("Include Table of Contents", value=True)
            
            # Sections to include
            st.write("Sections to Include:")
            col1, col2 = st.columns(2)
            with col1:
                include_overview = st.checkbox("Overview", value=True)
                include_installation = st.checkbox("Installation", value=True)
                include_api = st.checkbox("API Reference", value=True)
            with col2:
                include_examples = st.checkbox("Examples", value=True)
                include_architecture = st.checkbox("Architecture", value=False)
                include_contribution = st.checkbox("Contribution Guide", value=False)
        
        with tab3:
            st.subheader("Style Options")
            
            # Writing style
            writing_style = st.select_slider(
                "Writing Style",
                options=["Technical", "Balanced", "Conversational"],
                value="Balanced"
            )
            
            # Audience level
            audience = st.select_slider(
                "Target Audience",
                options=["Beginner", "Intermediate", "Advanced"],
                value="Intermediate"
            )
            
            # Code examples
            code_example_amount = st.select_slider(
                "Code Examples",
                options=["Minimal", "Moderate", "Extensive"],
                value="Moderate"
            )
        
        with tab4:
            st.subheader("AI Model Settings")
            
            # AI model selection
            model = st.selectbox(
                "Model",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                index=0,
                help="Select which AI model to use for documentation generation"
            )
            
            # Create columns for parameter inputs
            col1, col2 = st.columns(2)
            
            with col1:
                # Temperature
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1,
                    help="Higher values make output more random, lower values more deterministic"
                )
                
                # Top P
                top_p = st.slider(
                    "Top P",
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0,
                    step=0.1,
                    help="Controls diversity via nucleus sampling: 0.5 means half of all likelihood-weighted options are considered"
                )
                
                # Max tokens
                max_tokens = st.slider(
                    "Max Tokens",
                    min_value=100,
                    max_value=4000,
                    value=512,
                    step=100,
                    help="Maximum number of tokens in the generated documentation"
                )
            
            with col2:
                # Presence penalty
                presence_penalty = st.slider(
                    "Presence Penalty",
                    min_value=-2.0,
                    max_value=2.0,
                    value=0.0,
                    step=0.1,
                    help="Positive values penalize new tokens based on whether they appear in the text so far"
                )
                
                # Frequency penalty
                frequency_penalty = st.slider(
                    "Frequency Penalty",
                    min_value=-2.0,
                    max_value=2.0,
                    value=0.0,
                    step=0.1,
                    help="Positive values penalize tokens that have already appeared in the text based on their frequency"
                )
                
                # Seed for reproducibility
                use_seed = st.checkbox("Use Random Seed", value=False, 
                                    help="Enable for reproducible outputs")
                
                seed = None
                if use_seed:
                    seed = st.number_input("Seed Value", value=42, 
                                        help="Specific seed for reproducible results")
            
            # Stop sequences
            st.subheader("Advanced Settings")
            stop_sequences = st.text_area(
                "Stop Sequences (one per line)",
                "",
                help="The model will stop generating at any of these sequences (leave empty for default behavior)"
            )
        
        with tab5:
            st.subheader("Import Configuration")
            st.write("Import a previously saved configuration to quickly set up your documentation.")
            
            # Method selector for import
            import_method = st.radio(
                "Choose Import Method",
                ["Upload JSON File", "Paste JSON Configuration"],
                horizontal=True
            )
            
            # Sample configuration for reference
            with st.expander("View Sample Configuration"):
                st.code('''
{
  "purpose": "API Reference",
  "detail_level": 3,
  "focus_areas": ["Code Structure", "Function Documentation"],
  "format": "Markdown",
  "sections": {
    "toc": true,
    "overview": true,
    "installation": true,
    "api": true,
    "examples": true,
    "architecture": false,
    "contribution": false
  },
  "style": "Balanced",
  "audience": "Intermediate",
  "code_examples": "Moderate"
}
                ''', language="json")
            
            # Upload file option
            if import_method == "Upload JSON File":
                uploaded_file = st.file_uploader("Upload Configuration File", type=["json"])
                if uploaded_file is not None:
                    st.success("File uploaded successfully! Click 'Apply Configuration' to use these settings.")
                    if st.button("Apply Configuration"):
                        st.info("Configuration would be applied here in the complete app.")
                        
            # Paste JSON option
            else:
                json_input = st.text_area(
                    "Paste JSON Configuration", 
                    height=250,
                    placeholder="Paste your configuration JSON here..."
                )
                if json_input.strip():
                    if st.button("Apply Pasted Configuration"):
                        try:
                            # This would validate the JSON in a real implementation
                            st.success("Configuration applied successfully!")
                        except:
                            st.error("Invalid JSON configuration. Please check the format and try again.")
            
            # Save current configuration option
            st.divider()
            st.subheader("Export Current Configuration")
            if st.button("Generate Configuration JSON"):
                # Create a sample configuration to show functionality
                config = {
                    "purpose": "API Reference",
                    "detail_level": 3,
                    "focus_areas": ["Code Structure", "Function Documentation"],
                    "format": "Markdown",
                    "sections": {
                        "toc": True,
                        "overview": True,
                        "installation": True,
                        "api": True,
                        "examples": True,
                        "architecture": False,
                        "contribution": False
                    },
                    "style": "Balanced",
                    "audience": "Intermediate",
                    "code_examples": "Moderate"
                }
                st.code(json.dumps(config, indent=2), language="json")
                st.info("Copy this configuration or save it to a file for future use.")
                # In a complete app, you might add a download button here
        
        # Generate button
        if st.button("Generate Advanced Documentation", type="primary"):
            # Update model parameters in session state based on UI inputs
            st.session_state.model_params = {
                "model": model,
                "temp": temperature, 
                "top_p": top_p,
                "max_tokens": max_tokens,
                "pp": presence_penalty, 
                "fp": frequency_penalty, 
                "seed": seed if use_seed else None,
                "stop": [seq.strip() for seq in stop_sequences.split('\n') if seq.strip()] if stop_sequences else None
            }
            
            # Store the content, structure, and style settings for the main inference prompt
            st.session_state.advanced_prompt_content = {
                "content": {
                    "purpose": doc_purpose,
                    "detail_level": detail_level,
                    "focus_areas": focus_areas,
                    "custom_instructions": custom_instructions
                },
                "structure": {
                    "format": doc_format,
                    "sections": {
                        "toc": include_toc,
                        "overview": include_overview,
                        "installation": include_installation,
                        "api": include_api,
                        "examples": include_examples,
                        "architecture": include_architecture,
                        "contribution": include_contribution
                    }
                },
                "style": {
                    "tone": writing_style,
                    "audience": audience,
                    "code_examples": code_example_amount
                }
            }
            
            formatted_user_prompt = format_advanced_prompt(st.session_state.advanced_prompt_content)
            ai_args = create_ai_args_namespace(st.session_state.model_params)
            
            generated_documentation = "Error: AI did not return content."
            try:
                with st.spinner(" Lightning Draft is thinking..."):
                    # Make the actual AI call
                    generated_documentation = asyncio.run(get_ai_response(formatted_user_prompt, SYSTEM, ai_args))
                st.success("Advanced documentation generated successfully!")
            except Exception as e:
                st.error(f"Error during AI documentation generation: {e}")
                generated_documentation = f"Error generating documentation: {e}"

            # Save documentation and configuration to session state
            st.session_state.documentation_content = generated_documentation
            st.session_state.documentation_generated = True
            st.session_state.documentation_config = {
                "prompt_content": st.session_state.advanced_prompt_content,
                "model_params": st.session_state.model_params
            }
            
            # Force a rerun to update the sidebar UI
            st.rerun()
            
            # Display configuration summary
            st.subheader("Configuration Summary")
            config_tab1, config_tab2 = st.tabs(["Advanced Prompt Content", "Model Parameters"])
            with config_tab1:
                st.write("These settings defined the content, structure, and style of your documentation:")
                st.json(st.session_state.advanced_prompt_content)
            with config_tab2:
                st.write("These parameters were used to tune the model behavior:")
                st.json(st.session_state.model_params)

            # Documentation preview
            st.subheader("Documentation Preview")
            st.markdown(generated_documentation)
            
            # Show Step 4 button for reviewing documentation
            if st.button("Go to Documentation Review"):
                on_review_documentation()

elif st.session_state.lightning_sprint_active:
    # Display text input for Lightning Sprint mode
    with repo_container:
        # Use markdown with HTML for centered headers
        st.markdown("<h1 style='text-align: center; color: grey;'> Lightning Sprint</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Quick Documentation Generation</h3>", unsafe_allow_html=True)
        st.divider()

        st.markdown("<p style='text-align: center;'>Enter a prompt for generating documentation based on your repository</p>", unsafe_allow_html=True)
        
        # Multi-line text input for the prompt
        user_prompt = st.text_area(
            "Prompt", 
            "Generate comprehensive documentation for this repository", 
            height=150,
            max_chars=1000,
            help="Be specific about what kind of documentation you want")
        
        # Submit button and options
        generate_pressed = st.button("Generate Quick Documentation", type="primary")
        
        # Handle generate button press
        if generate_pressed:
            # Store the prompt content for sprint mode
            st.session_state.sprint_prompt_content = {"prompt": user_prompt}
            
            ai_args = create_ai_args_namespace(st.session_state.sprint_model_params)
            
            generated_documentation = "Error: AI did not return content."
            try:
                with st.spinner(" Lightning Sprint is thinking..."):
                    # Prepare context with repository contents
                    if st.session_state.repo_contents:
                        # Create a context with repository structure and content
                        repo_context = f"\n\n### Repository Contents:\n"
                        
                        # Add file tree for structure overview
                        repo_path = "repo"
                        if os.path.exists(repo_path) and os.path.isdir(repo_path):
                            repo_tree = get_repo_file_tree(repo_path)
                            repo_context += f"\n\n### Repository Structure:\n```\n{repo_tree}\n```\n\n"
                        
                        # Count tokens in repo contents
                        all_content = json.dumps(st.session_state.repo_contents)
                        token_count = count_tokens(all_content)
                        
                        # If token count is manageable, include all file contents
                        # Otherwise, just include the structure and file names
                        MAX_TOKENS = 50000  # Set a reasonable limit
                        
                        if token_count < MAX_TOKENS:
                            repo_context += "\n\n### File Contents:\n"
                            for file_path, content in st.session_state.repo_contents.items():
                                repo_context += f"\n\n#### {file_path}\n```\n{content}\n```\n"
                        else:
                            # Just include file names if content is too large
                            st.warning(f"Repository content is too large ({token_count} tokens). Sending only structure information to the AI.")
                            repo_context += "\n\n### Files in repository:\n"
                            for file_path in st.session_state.repo_contents.keys():
                                repo_context += f"- {file_path}\n"
                        
                        # Combine user prompt with repository context
                        full_prompt = f"{user_prompt}\n\n{repo_context}"
                    else:
                        full_prompt = user_prompt
                        st.warning("No repository contents available. Documentation may be limited.")
                    
                    # Make the actual AI call with repository context
                    generated_documentation = asyncio.run(get_ai_response(full_prompt, SYSTEM, ai_args))
                st.success("Quick documentation generated successfully!")
            except Exception as e:
                st.error(f"Error during AI documentation generation: {e}")
                generated_documentation = f"Error generating documentation: {e}"

            # Save documentation and configuration to session state
            st.session_state.documentation_content = generated_documentation
            st.session_state.documentation_generated = True
            st.session_state.documentation_config = {
                "prompt_content": st.session_state.sprint_prompt_content,
                "model_params": st.session_state.sprint_model_params
            }
            
            # Force a rerun to update the sidebar UI
            st.rerun()
            
            # Display configuration summary
            with st.expander("View Configuration Summary"):
                config_tab1, config_tab2 = st.tabs(["Prompt Content", "Model Parameters"])
                with config_tab1:
                    st.write("This prompt was used for generation:")
                    st.json(st.session_state.sprint_prompt_content)
                with config_tab2:
                    st.write("These parameters were used to tune the model behavior:")
                    st.json(st.session_state.sprint_model_params)
            
            # Display generated documentation
            st.markdown("<h1 style='text-align: center; color: grey;'>Generated Documentation</h1>", unsafe_allow_html=True)
            st.divider()
            st.markdown(generated_documentation)
            
            # Show Step 4 button for reviewing documentation
            if st.button("Go to Documentation Review"):
                on_review_documentation()

# Only display repository contents when examine button was clicked and Lightning Sprint isn't active
elif st.session_state.show_repo_contents:
    with repo_container:
        repo_path = "repo"
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            # Use markdown with HTML for centered and grey header
            st.markdown("<h1 style='text-align: center; color: grey;'>Repository Contents</h1>", unsafe_allow_html=True)
            
            # Display token count information for the repository contents
            if st.session_state.repo_contents:
                num_files = len(st.session_state.repo_contents)
                all_content = json.dumps(st.session_state.repo_contents)
                token_count = count_tokens(all_content)
                
                st.info(f"Repository contains {num_files} files with approximately {token_count:,} tokens.")
            
            # Get statistics about the repository
            file_count = sum([len(files) for _, _, files in os.walk(repo_path)])
            dir_count = sum([len(dirs) for _, dirs, _ in os.walk(repo_path)])
            
            st.info(f"Repository contains {file_count} files in {dir_count} directories.")
            
            # Create tabs for different views of the repository
            file_tab, tree_tab, contents_tab = st.tabs(["📁 File Explorer", "🌳 Tree View", "📚 Content Stats"])
            
            with file_tab:
                st.write("Viewing files in the 'repo' folder:")
                # Display the directory structure using the original function
                display_directory_contents(repo_path)
                
            with tree_tab:
                st.write("Repository folder structure tree:")
                # Display the formatted tree view using our new function
                repo_tree = get_repo_file_tree(repo_path)
                st.code(repo_tree)
                
            with contents_tab:
                st.write("Repository file contents:")
                if st.session_state.repo_contents:
                    st.json(st.session_state.repo_contents)
                else:
                    st.info("No repository contents available.")
        else:
            st.warning("No repository found. Please pull a repository first using Step 1.")
else:
    # Show welcome screen with lightning animation when no option is active
    with repo_container:
        st.markdown('''
<div class="welcome-container">
    <div style="display: flex; justify-content: center;">
        <div class="lightning-bolt">⚡</div>
        <div class="lightning-bolt">⚡</div>
        <div class="lightning-bolt">⚡</div>
    </div>
    <h2>Welcome to Lightning MD</h2>
    <div class="welcome-text">
        <p>Generate beautiful documentation from your GitHub repositories with lightning speed!</p>
        <p>Get started by entering a GitHub repository URL and clicking "Pull Repository" in the sidebar.</p>
    </div>
</div>
        ''', unsafe_allow_html=True)