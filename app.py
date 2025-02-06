import streamlit as st
import tempfile
import subprocess
import os
import shutil
import logging
import re
import json
import pyperclip

from docs_factory import generate_readme  # Import the generate_readme function
from manual_edit import manual_edit_page  # Import the manual edit page


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize session state for temp_dir, readable_files, and readme_content
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'readable_files' not in st.session_state:
    st.session_state.readable_files = {}
if 'readme_content' not in st.session_state:
    st.session_state.readme_content = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None

with st.sidebar:
    st.title("Auto README Generator")
    st.subheader("Easily generate a README.md file for your project.")
    st.write(
        "Are you tired of writing documentation? "
        "Simply enter your public GitHub repository URL and let this tool clone your repo, analyze your files, "
        "and generate a comprehensive README for you automatically."
    )
    st.markdown("---")
    st.write("Step 1. Pull Your GitHub Project Repo")
    st.write("Clone your repository into a temporary directory to process its contents.")
    st.markdown("---")
    st.write("Step 2. Generate README.md")
    st.write("Generate a detailed README file based on your repository's readable files.")
    st.markdown("---")
    st.write("Step 3. Manage Your Generated README.md")
    st.write("Edit, copy, download, or push your new README to your repository.")
    st.markdown("---")
    

github_url = st.text_input("Enter your public GitHub repo URL (HTTPS format recommended)")

# Define a regex pattern for validating GitHub HTTPS URLs ending with .git
url_pattern = r'^https://github\.com\/[\w\-]+\/[\w\-]+\.git$'

if github_url:
    st.write("Step 1. Pull Your GitHub Project Repo")
    
    # Validate the GitHub URL
    if not re.match(url_pattern, github_url):
        st.error("Please enter a valid GitHub repository URL in the format: `https://github.com/username/repository.git`")
    else:
        if st.button("Pull Repo"):
            st.write(f"Requesting to pull your repo: {github_url}")
            try:
                # Create a temporary directory
                temp_dir = tempfile.mkdtemp()
                st.session_state.temp_dir = temp_dir
                st.write(f"Cloning repository into temporary directory: {temp_dir}")

                # Execute the git clone command using HTTPS
                with st.spinner("Cloning repository..."):
                    clone_result = subprocess.run(
                        ["git", "clone", github_url, temp_dir],
                        capture_output=True,
                        text=True
                    )

                if clone_result.returncode != 0:
                    st.error(f"Error cloning repository:\n{clone_result.stderr}")
                    logger.error(f"Git Clone Error: {clone_result.stderr}")
                    shutil.rmtree(temp_dir)  # Cleanup on failure
                    st.session_state.temp_dir = None
                else:
                    st.success("Repository successfully cloned!")
                    logger.info("Repository successfully cloned.")

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

                    if readable_files:
                        st.write("### Readable Files in the Repository:")
                        for file, content in readable_files.items():
                            st.write(f"- {file}")
                            with st.expander(f"View content of {file}"):
                                st.code(content, language='python')  # Specify the language as needed
                    else:
                        st.write("No readable files found in the repository.")

            except subprocess.CalledProcessError as e:
                st.error(f"An error occurred while cloning the repository: {e}")
                logger.exception("Git Clone Failed")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logger.exception("Unexpected Error during Cloning")

# Step 2: Generate README.md and Display It Permanently in This Section
if st.session_state.readable_files:
    st.write("Step 2. Generate Your New README File")
    st.text_input("AI instruction (optional) (coming soon)")
    if st.button("Generate README.md"):
        try:
            temp_dir = st.session_state.temp_dir
            readable_files = st.session_state.readable_files

            if temp_dir and readable_files:
                # Generate README content using the Anthropic model
                readme_content = generate_readme(readable_files)
                st.session_state.readme_content = readme_content

                # Path for the README.md
                readme_path = os.path.join(temp_dir, "README.md")

                # Write the generated content to README.md
                with open(readme_path, 'w', encoding='utf-8') as readme_file:
                    readme_file.write(readme_content)

                st.success(f"README.md has been generated at `{readme_path}`.")
            else:
                st.error("No readable files available to generate README.")
        except Exception as e:
            st.error(f"An error occurred while generating README: {e}")
            logger.exception("README Generation Failed")
    
    # Below the Generate button, always display the current README.md content if it exists in session.
    if st.session_state.get("readme_content"):
        st.markdown("### Current README.md")
        st.text_area("Current README.md", st.session_state.readme_content, height=600, disabled=True)

# Display the Push to Repository section only if README has been generated
if st.session_state.readme_content and st.session_state.temp_dir:
    st.write("Step 3. Manage Your Generated README.md")

    # Always show the Edit button. When pressed, the manual edit mode is enabled.
    if st.button("Edit README.md"):

        st.session_state.edit_mode = "manual_edit"

    if st.session_state.get("edit_mode") == "manual_edit":
        # When in edit mode, show only the manual editor (and a Finish Editing button to exit edit mode)
        st.write("### Manual Editing Mode")
        updated_content = manual_edit_page(st.session_state.readme_content)
        if st.button("Finish Editing"):
            st.session_state.readme_content = updated_content
            st.session_state.edit_mode = None
            st.rerun()

        if st.button("View README.md"):
            st.markdown("---")
            st.button("Close View", key="1")
            content = st.session_state.readme_content
            st.markdown(content)
            st.button("Close View", key="2")



    else:
        # Only display these buttons if NOT in edit mode.
        if st.button("Copy to clipboard"):

            readme = st.session_state.readme_content
            pyperclip.copy(readme)
            st.success("README.md has been copied to the clipboard!")



        st.download_button(
            label="Download README.md",
            data=st.session_state.readme_content,
            file_name="README.md",
            mime="text/markdown"
        )

        if st.button("Push to Repository"):
            st.write("Experimental feature. May not work as expected.")
            try:
                temp_dir = st.session_state.temp_dir

                if temp_dir:
                    # Navigate to the temporary directory
                    original_dir = os.getcwd()
                    os.chdir(temp_dir)

                    # Configure Git user if not already set
                    subprocess.run(["git", "config", "user.name", "Auto README Generator"], check=True)
                    subprocess.run(["git", "config", "user.email", "auto-README-generator@example.com"], check=True)

                    # Stage the README.md file
                    add_result = subprocess.run(
                        ["git", "add", "README.md"],
                        capture_output=True,
                        text=True
                    )
                    if add_result.returncode != 0:
                        st.error(f"Error adding README.md to git:\n{add_result.stderr}")
                        logger.error(f"Git Add Error: {add_result.stderr}")
                        os.chdir(original_dir)
                    else:
                        logger.info("README.md added to staging area.")

                    # Commit the changes
                    commit_message = "Add generated README.md - Automated Commit"
                    commit_result = subprocess.run(
                        ["git", "commit", "-m", commit_message],
                        capture_output=True,
                        text=True
                    )
                    if commit_result.returncode != 0:
                        st.error(f"Error committing README.md:\n{commit_result.stderr}")
                        logger.error(f"Git Commit Error: {commit_result.stderr}")
                        os.chdir(original_dir)
                    else:
                        st.success("README.md has been committed.")
                        logger.info("README.md committed successfully.")

                    # Push the changes to the remote repository
                    with st.spinner("Pushing README.md to the repository..."):
                        push_result = subprocess.run(
                            ["git", "push"],
                            capture_output=True,
                            text=True
                        )

                    if push_result.returncode != 0:
                        st.error(f"Error pushing to repository:\n{push_result.stderr}")
                        logger.error(f"Git Push Error: {push_result.stderr}")
                    else:
                        st.success("README.md has been successfully pushed to the repository.")
                        logger.info("README.md pushed successfully.")

                    # Cleanup: Attempt to remove the temporary directory
                    try:
                        os.chdir(original_dir)
                        shutil.rmtree(temp_dir)
                        st.write("Temporary directory has been cleaned up.")
                        # Reset session state
                        st.session_state.temp_dir = None
                        st.session_state.readable_files = {}
                        st.session_state.readme_content = None
                        st.session_state.edit_mode = None
                    except PermissionError as pe:
                        st.warning(f"Could not delete temporary directory automatically: {pe}")
                        st.info(f"Please delete the temporary directory manually: `{temp_dir}`")
                else:
                    st.error("Temporary directory not found.")
            except subprocess.CalledProcessError as e:
                st.error(f"An error occurred while pushing the README to the repository: {e}")
                logger.exception("Git Push Failed")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logger.exception("Unexpected Error during Push")
