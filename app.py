import streamlit as st
import tempfile
import subprocess
import os
import shutil
import logging

from docs_factory import generate_readme  # Import the generate_readme function

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


with st.sidebar:
    st.title("Auto README Generator")
    st.subheader("Easily generate a README.md file for your project.")
    st.markdown("---")
    st.write("Tired of documentation? Let me do it for you! I will pull your files from github and generate documentation based off of your projects")

github_url = st.text_input("Enter your public GitHub repo URL (SSH format recommended)")

if github_url:
    st.write("Step 1. Pull Your Github Project Repo")
    if st.button("Pull Repo"):
        st.write(f"Requesting to pull your repo: {github_url}")
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            st.session_state.temp_dir = temp_dir
            st.write(f"Cloning repository into temporary directory: {temp_dir}")

            # Execute the git clone command
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

# Display the Generate README button only if there are readable files
if st.session_state.readable_files:
    st.write("Step 2. Generate Your New README File")
    if st.button("Generate README"):
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

                # Provide a download link for the README.md
                st.download_button(
                    label="Download README.md",
                    data=readme_content,
                    file_name="README.md",
                    mime="text/markdown"
                )

                # Display the generated README with enhanced styling
                st.markdown("### Generated README.md")
                st.markdown("---")
                st.markdown(readme_content, unsafe_allow_html=True)
            else:
                st.error("No readable files available to generate README.")
        except Exception as e:
            st.error(f"An error occurred while generating README: {e}")
            logger.exception("README Generation Failed")

# Display the Push to Repository button only if README has been generated
if st.session_state.readme_content and st.session_state.temp_dir:
    st.write("Step 3. Push Your New README File to Github and enjoy!")
    if st.button("Push to Repository"):
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