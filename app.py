import streamlit as st
import tempfile
import subprocess
import os
import shutil
import logging
import re
import json
import pyperclip
from datetime import datetime

from docs_factory import generate_readme
from manual_edit import manual_edit_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Lightning MD - Generate Professional README.md Files",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main Theme Colors */
    :root {
        --primary-color: #4F8BF9;
        --secondary-color: #1E88E5;
        --background-color: #FAFAFA;
        --success-color: #4CAF50;
        --warning-color: #FFC107;
        --error-color: #F44336;
    }
    
    /* Header Styling */
    .main-header {
        color: #1E88E5;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .sub-header {
        color: #424242;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* Card Styling */
    .card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Step Indicator */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        position: relative;
    }
    
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 2;
    }
    
    .step-number {
        width: 30px;
        height: 30px;
        background-color: #E0E0E0;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        margin-bottom: 8px;
    }
    
    .step-active .step-number {
        background-color: #1E88E5;
        color: white;
    }
    
    .step-text {
        font-size: 0.8rem;
        color: #757575;
        text-align: center;
    }
    
    .step-active .step-text {
        color: #1E88E5;
        font-weight: 500;
    }
    
    /* Icon Styling */
    .icon {
        margin-right: 8px;
        vertical-align: middle;
    }
    
    /* File List Styling */
    .file-item {
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 4px;
        background-color: #F5F5F5;
        font-family: monospace;
    }
    
    /* Footer Styling */
    .footer {
        text-align: center;
        color: #9E9E9E;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E0E0E0;
    }
    
    /* Center images */
    .centered-image {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Custom section divider */
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, rgba(79,139,249,0.2) 0%, rgba(30,136,229,0.8) 50%, rgba(79,139,249,0.2) 100%);
        margin: 1.5rem 0;
        border-radius: 2px;
    }
    
    /* Text area customization */
    .stTextArea textarea {
        height: 400px;
        background-color: #F5F5F5;
        border-radius: 5px;
        font-family: monospace;
        color: #333333 !important;
    }
    
    /* Status Messages */
    .success-box {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4CAF50;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    
    .error-box {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #F44336;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    
    .info-box {
        background-color: rgba(33, 150, 243, 0.1);
        border-left: 4px solid #2196F3;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }
        .sub-header {
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for temp_dir, readable_files, and readme_content
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'readable_files' not in st.session_state:
    st.session_state.readable_files = {}
if 'readme_content' not in st.session_state:
    st.session_state.readme_content = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None
if 'active_step' not in st.session_state:
    st.session_state.active_step = 1

# Determine which step is active
def get_step_status(step_number):
    if st.session_state.active_step >= step_number:
        return "step-active"
    return ""

# Display step indicator
def display_step_indicator():
    st.markdown(
        f"""
        <div class="step-container">
            <div class="step-item {get_step_status(1)}">
                <div class="step-number">1</div>
                <div class="step-text">Pull Repo</div>
            </div>
            <div class="step-item {get_step_status(2)}">
                <div class="step-number">2</div>
                <div class="step-text">Generate README</div>
            </div>
            <div class="step-item {get_step_status(3)}">
                <div class="step-number">3</div>
                <div class="step-text">Manage README</div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Sidebar content
with st.sidebar:
    st.image("autodock logo.webp", width=200, use_column_width=True)
    
    st.markdown("<h2 style='text-align: center;'>Lightning MD</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <p>Transform your projects with professional documentation in seconds!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <h4>How It Works:</h4>
    
    <p><b>Step 1:</b> Pull your GitHub repository</p>
    <p class="info-box">Enter your repository URL and let us analyze your codebase.</p>
    
    <p><b>Step 2:</b> Generate README</p>
    <p class="info-box">Our AI generates a comprehensive README based on your code.</p>
    
    <p><b>Step 3:</b> Manage README</p>
    <p class="info-box">Edit, download, or push your README directly to your repository.</p>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer">
        <p>© {0} Lightning MD</p>
        <p>Making documentation effortless</p>
    </div>
    """.format(datetime.now().year), unsafe_allow_html=True)

# Main content
st.markdown('<h1 class="main-header">Lightning MD</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Create professional README files in seconds ⚡</p>', unsafe_allow_html=True)

# Display step indicator
display_step_indicator()

# Main app sections
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📦 Repository Details")
    github_url = st.text_input(
        "Enter your public GitHub repo URL (HTTPS format)",
        placeholder="https://github.com/username/repository.git"
    )

    # Define a regex pattern for validating GitHub HTTPS URLs ending with .git
    url_pattern = r'^https://github\.com\/[\w\-]+\/[\w\-]+\.git$'

    if github_url:
        # Validate the GitHub URL
        if not re.match(url_pattern, github_url):
            st.markdown(
                '<div class="error-box">Please enter a valid GitHub repository URL in the format: <code>https://github.com/username/repository.git</code></div>',
                unsafe_allow_html=True
            )
        else:
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                pull_button = st.button("🔄 Pull Repository", use_container_width=True)
            with col_btn2:
                if st.session_state.readable_files:
                    clear_button = st.button("🗑️ Clear Data", use_container_width=True)
                    if clear_button:
                        # Cleanup temporary directory if it exists
                        if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
                            try:
                                shutil.rmtree(st.session_state.temp_dir)
                            except Exception as e:
                                logger.error(f"Error cleaning up temp directory: {e}")
                        
                        # Reset session state
                        st.session_state.temp_dir = None
                        st.session_state.readable_files = {}
                        st.session_state.readme_content = None
                        st.session_state.edit_mode = None
                        st.session_state.active_step = 1
                        st.rerun()
            
            if pull_button:
                try:
                    with st.spinner("🔍 Cloning repository..."):
                        # Create a temporary directory
                        temp_dir = tempfile.mkdtemp()
                        st.session_state.temp_dir = temp_dir
                        
                        # Execute the git clone command using HTTPS
                        clone_result = subprocess.run(
                            ["git", "clone", github_url, temp_dir],
                            capture_output=True,
                            text=True
                        )

                        if clone_result.returncode != 0:
                            st.markdown(
                                f'<div class="error-box">⚠️ Error cloning repository:<br><code>{clone_result.stderr}</code></div>',
                                unsafe_allow_html=True
                            )
                            logger.error(f"Git Clone Error: {clone_result.stderr}")
                            shutil.rmtree(temp_dir)  # Cleanup on failure
                            st.session_state.temp_dir = None
                        else:
                            st.markdown(
                                '<div class="success-box">✅ Repository successfully cloned!</div>',
                                unsafe_allow_html=True
                            )
                            logger.info("Repository successfully cloned.")
                            
                            # Update active step
                            st.session_state.active_step = 2

                            # Initialize a dictionary to store readable file paths and their contents
                            readable_files = {}

                            # Walk through the directory, excluding the .git folder
                            for root, dirs, files in os.walk(temp_dir):
                                # Skip the .git directory
                                if '.git' in dirs:
                                    dirs.remove('.git')  # Prevents os.walk from traversing the .git directory

                                for file in files:
                                    file_path = os.path.join(root, file)
                                    try:
                                        # Attempt to open the file in text mode to check if it's readable
                                        with open(file_path, 'r', encoding='utf-8') as f:
                                            file_content = f.read()  # Read the file content
                                        # Get the relative path for better readability
                                        relative_path = os.path.relpath(file_path, temp_dir)
                                        readable_files[relative_path] = file_content
                                    except (UnicodeDecodeError, PermissionError):
                                        # Skip files that are not readable (e.g., binary files or permission issues)
                                        continue

                            # Update session state with readable files and their contents
                            st.session_state.readable_files = readable_files
                            st.rerun()

                except subprocess.CalledProcessError as e:
                    st.markdown(
                        f'<div class="error-box">⚠️ An error occurred while cloning the repository: {e}</div>',
                        unsafe_allow_html=True
                    )
                    logger.exception("Git Clone Failed")
                except Exception as e:
                    st.markdown(
                        f'<div class="error-box">⚠️ An unexpected error occurred: {e}</div>',
                        unsafe_allow_html=True
                    )
                    logger.exception("Unexpected Error during Cloning")
    st.markdown('</div>', unsafe_allow_html=True)

# Display repository details if available
if st.session_state.readable_files:
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📂 Repository Files")
        
        # Group files by extension
        file_extensions = {}
        for file_path in st.session_state.readable_files.keys():
            ext = os.path.splitext(file_path)[1].lower()
            if not ext:
                ext = "(no extension)"
            if ext not in file_extensions:
                file_extensions[ext] = []
            file_extensions[ext].append(file_path)
        
        # Create tabs for each file extension group
        if file_extensions:
            tabs = st.tabs([f"{ext} ({len(files)})" for ext, files in file_extensions.items()])
            
            for i, (ext, files) in enumerate(file_extensions.items()):
                with tabs[i]:
                    for file_path in sorted(files):
                        with st.expander(file_path):
                            content = st.session_state.readable_files[file_path]
                            # Determine language for syntax highlighting
                            extension = os.path.splitext(file_path)[1].lower()
                            if extension in ['.py']:
                                language = 'python'
                            elif extension in ['.js', '.jsx', '.ts', '.tsx']:
                                language = 'javascript'
                            elif extension in ['.html']:
                                language = 'html'
                            elif extension in ['.css']:
                                language = 'css'
                            elif extension in ['.md']:
                                language = 'markdown'
                            elif extension in ['.json']:
                                language = 'json'
                            else:
                                language = None
                            
                            st.code(content, language=language)
        else:
            st.info("No readable files found in the repository.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Generate README.md")
        
        optional_prompt = st.text_area(
            "AI Instructions (Optional)",
            placeholder="Add any specific instructions for the AI, such as 'Focus on installation steps' or 'Highlight the API endpoints'"
        )
        
        if st.button("⚡ Generate README.md", use_container_width=True):
            try:
                with st.spinner("✨ Generating your README.md..."):
                    temp_dir = st.session_state.temp_dir
                    readable_files = st.session_state.readable_files

                    if temp_dir and readable_files:
                        # Generate README content using the Anthropic model
                        readme_content = generate_readme(readable_files, optional_prompt)
                        st.session_state.readme_content = readme_content

                        # Path for the README.md
                        readme_path = os.path.join(temp_dir, "README.md")

                        # Write the generated content to README.md
                        with open(readme_path, 'w', encoding='utf-8') as readme_file:
                            readme_file.write(readme_content)

                        st.markdown(
                            '<div class="success-box">✅ README.md has been successfully generated!</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Update active step
                        st.session_state.active_step = 3
                        st.rerun()
                    else:
                        st.markdown(
                            '<div class="error-box">⚠️ No readable files available to generate README.</div>',
                            unsafe_allow_html=True
                        )
            except Exception as e:
                st.markdown(
                    f'<div class="error-box">⚠️ An error occurred while generating README: {e}</div>',
                    unsafe_allow_html=True
                )
                logger.exception("README Generation Failed")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Display and manage README content if available
if st.session_state.readme_content and st.session_state.temp_dir:
    if st.session_state.get("edit_mode") == "manual_edit":
        # When in edit mode, show only the manual editor
        updated_content = manual_edit_page(st.session_state.readme_content)
        
        col_back, col_save, col_preview = st.columns([1, 1, 1])
        
        with col_back:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.edit_mode = None
                st.rerun()
        
        with col_save:
            if st.button("💾 Save Changes", use_container_width=True):
                st.session_state.readme_content = updated_content
                st.session_state.edit_mode = None
                
                # Update the README.md file in the temp directory
                readme_path = os.path.join(st.session_state.temp_dir, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as readme_file:
                    readme_file.write(updated_content)
                
                st.markdown(
                    '<div class="success-box">✅ Changes saved successfully!</div>',
                    unsafe_allow_html=True
                )
                st.rerun()
        
        with col_preview:
            preview_toggle = st.toggle("👁️ Preview", value=False)
            if preview_toggle:
                st.markdown("### README Preview")
                st.markdown(updated_content)
    else:
        # Display README content and action buttons
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📄 Generated README.md")
            
            with st.expander("View README Content", expanded=True):
                st.markdown(st.session_state.readme_content)
            
            # Action buttons
            col_edit, col_copy, col_download, col_push = st.columns([1, 1, 1, 1])
            
            with col_edit:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.edit_mode = "manual_edit"
                    st.rerun()
            
            with col_copy:
                if st.button("📋 Copy", use_container_width=True):
                    readme = st.session_state.readme_content
                    pyperclip.copy(readme)
                    st.markdown(
                        '<div class="success-box">✅ README.md has been copied to clipboard!</div>',
                        unsafe_allow_html=True
                    )
            
            with col_download:
                st.download_button(
                    label="💾 Download",
                    data=st.session_state.readme_content,
                    file_name="README.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col_push:
                if st.button("🚀 Push to Repo", use_container_width=True):
                    st.markdown(
                        '<div class="info-box">ℹ️ Experimental feature. May not work as expected.</div>',
                        unsafe_allow_html=True
                    )
                    try:
                        with st.spinner("🔄 Pushing README.md to repository..."):
                            temp_dir = st.session_state.temp_dir

                            if temp_dir:
                                # Navigate to the temporary directory
                                original_dir = os.getcwd()
                                os.chdir(temp_dir)

                                # Configure Git user if not already set
                                subprocess.run(["git", "config", "user.name", "Lightning MD Generator"], check=True)
                                subprocess.run(["git", "config", "user.email", "lightning-md-generator@example.com"], check=True)

                                # Stage the README.md file
                                add_result = subprocess.run(
                                    ["git", "add", "README.md"],
                                    capture_output=True,
                                    text=True
                                )
                                if add_result.returncode != 0:
                                    st.markdown(
                                        f'<div class="error-box">⚠️ Error adding README.md to git:<br><code>{add_result.stderr}</code></div>',
                                        unsafe_allow_html=True
                                    )
                                    logger.error(f"Git Add Error: {add_result.stderr}")
                                    os.chdir(original_dir)
                                else:
                                    logger.info("README.md added to staging area.")

                                    # Commit the changes
                                    commit_message = "Add generated README.md - Generated by Lightning MD"
                                    commit_result = subprocess.run(
                                        ["git", "commit", "-m", commit_message],
                                        capture_output=True,
                                        text=True
                                    )
                                    if commit_result.returncode != 0:
                                        st.markdown(
                                            f'<div class="error-box">⚠️ Error committing README.md:<br><code>{commit_result.stderr}</code></div>',
                                            unsafe_allow_html=True
                                        )
                                        logger.error(f"Git Commit Error: {commit_result.stderr}")
                                        os.chdir(original_dir)
                                    else:
                                        st.markdown(
                                            '<div class="success-box">✅ README.md has been committed.</div>',
                                            unsafe_allow_html=True
                                        )
                                        logger.info("README.md committed successfully.")

                                        # Push the changes to the remote repository
                                        push_result = subprocess.run(
                                            ["git", "push"],
                                            capture_output=True,
                                            text=True
                                        )

                                        if push_result.returncode != 0:
                                            st.markdown(
                                                f'<div class="error-box">⚠️ Error pushing to repository:<br><code>{push_result.stderr}</code></div>',
                                                unsafe_allow_html=True
                                            )
                                            logger.error(f"Git Push Error: {push_result.stderr}")
                                        else:
                                            st.markdown(
                                                '<div class="success-box">✅ README.md has been successfully pushed to the repository.</div>',
                                                unsafe_allow_html=True
                                            )
                                            logger.info("README.md pushed successfully.")

                                # Cleanup: Attempt to remove the temporary directory
                                try:
                                    os.chdir(original_dir)
                                    shutil.rmtree(temp_dir)
                                    st.markdown(
                                        '<div class="info-box">ℹ️ Temporary directory has been cleaned up.</div>',
                                        unsafe_allow_html=True
                                    )
                                    # Reset session state
                                    st.session_state.temp_dir = None
                                    st.session_state.readable_files = {}
                                    st.session_state.readme_content = None
                                    st.session_state.edit_mode = None
                                    st.session_state.active_step = 1
                                except PermissionError as pe:
                                    st.markdown(
                                        f'<div class="warning-box">⚠️ Could not delete temporary directory automatically: {pe}<br>Please delete manually: <code>{temp_dir}</code></div>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.markdown(
                                    '<div class="error-box">⚠️ Temporary directory not found.</div>',
                                    unsafe_allow_html=True
                                )
                    except subprocess.CalledProcessError as e:
                        st.markdown(
                            f'<div class="error-box">⚠️ An error occurred while pushing the README to the repository: {e}</div>',
                            unsafe_allow_html=True
                        )
                        logger.exception("Git Push Failed")
                    except Exception as e:
                        st.markdown(
                            f'<div class="error-box">⚠️ An unexpected error occurred: {e}</div>',
                            unsafe_allow_html=True
                        )
                        logger.exception("Unexpected Error during Push")
            
            st.markdown('</div>', unsafe_allow_html=True)

# Only show this on the initial page or when no major operations are running
if not st.session_state.readable_files:
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### ⚡ Key Features")
        
        features = [
            "AI-powered README generation",
            "GitHub repository integration",
            "Edit and preview functionality",
            "One-click push to repository",
            "Multiple file format support",
            "Custom styling and formatting"
        ]
        
        for feature in features:
            st.markdown(f"✓ {feature}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💡 Tips")
        
        st.markdown("""
        - Use HTTPS URLs for best compatibility
        - Add custom instructions for tailored READMEs
        - Preview before pushing to your repository
        - Check repository permissions if push fails
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
