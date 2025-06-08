#!/usr/bin/env python3

#################################################
# PULL REPO
#################################################

import os
import sys
import subprocess
import shutil

def clone_github_repo(github_url):
    """
    Clones a public GitHub repository to a folder named 'repo'
    
    Args:
        github_url (str): URL of the GitHub repository to clone
        
    Raises:
        subprocess.CalledProcessError: If git clone command fails
        Exception: For other unexpected errors
        
    Returns:
        bool: True if repository was cloned successfully
    """
    # Get the target directory name
    repo_dir = "repo"
    
    # Handle existing repository by renaming instead of deleting
    if os.path.exists(repo_dir):
        print(f"Handling existing '{repo_dir}' directory...")
        try:
            # Rename the existing repo to a backup name temporarily
            temp_dir = f"{repo_dir}_old"
            
            # Remove any previous backup if it exists
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
            # Rename the current repo to backup
            os.rename(repo_dir, temp_dir)
            
            # Try to remove the backup directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Removed old repository directory")
            except:
                # If we can't remove it, that's fine, we've already renamed it
                print(f"Note: Could not remove old repository backup, but continuing with clone")
        except Exception as e:
            print(f"Warning handling existing repository: {e}")
            # Continue even if we couldn't handle the old repo
    
    # Create a new empty repo directory
    try:
        os.makedirs(repo_dir, exist_ok=True)
    except Exception as e:
        error_msg = f"Could not create repository directory: {str(e)}"
        print(f"Error: {error_msg}")
        raise Exception(error_msg)
    
    try:
        # Clone the repository
        print(f"Cloning {github_url} into '{repo_dir}'...")
        subprocess.run(["git", "clone", github_url, repo_dir], check=True)
        print("Repository cloned successfully!")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to clone repository. Make sure the URL is correct and you have git installed. Command returned: {e}"
        print(f"Error: {error_msg}")
        raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, e.stderr, error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred during cloning: {str(e)}"
        print(f"Error: {error_msg}")
        raise Exception(error_msg)

def main(github_url=None):
    """Main function that can be called by other modules or run directly"""
    if github_url is None:
        print("Usage: python pull_repo.py <github_repository_url>")
        print("Example: python pull_repo.py https://github.com/username/repository.git")
        return False
    
    try:
        success = clone_github_repo(github_url)
        return success
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        return False

if __name__ == "__main__":
    # If script is run directly, prompt user for GitHub URL
    if len(sys.argv) > 1:
        # If URL was provided as command-line argument, use it
        github_url = sys.argv[1]
    else:
        # Otherwise prompt for URL input
        github_url = input("Enter GitHub repository URL: ")
    
    if github_url.strip():
        main(github_url)
    else:
        print("No URL provided. Exiting.")
        sys.exit(1)






#################################################
# READ LOCAL REPO
#################################################

# Scan the local repo folder and extract all file contents

import os
import json
import chardet

def get_local_repo_contents(repo_path='./repo'):
    """
    Scans a local repository folder and returns a dictionary with file paths as keys
    and their raw contents as values.
    
    Args:
        repo_path: Path to the local repository folder, defaults to './repo'
        
    Returns:
        Dictionary with relative file paths as keys and file contents as values
    """
    # Normalize and get absolute path
    repo_path = os.path.abspath(repo_path)
    
    if not os.path.exists(repo_path):
        print(f"Repository folder not found: {repo_path}")
        return {}
        
    file_contents = {}
    binary_extensions = [
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',  # Images
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',  # Documents
        '.zip', '.tar', '.gz', '.rar', '.7z',  # Archives
        '.exe', '.dll', '.so', '.dylib',  # Binaries
        '.pyc', '.pyo', '.pyd',  # Python compiled
        '.jar', '.war', '.ear',  # Java
        '.mp3', '.mp4', '.avi', '.mov', '.flv',  # Media
    ]
    
    # Keep track of files processed for reporting
    total_files = 0
    processed_files = 0
    skipped_files = 0
    
    print(f"Scanning repository folder: {repo_path}")
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories (typically .git, node_modules, etc.)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        dirs[:] = [d for d in dirs if d != 'node_modules']
        
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            
            # Skip hidden files
            if file.startswith('.'):
                skipped_files += 1
                continue
                
            # Check file extension
            _, ext = os.path.splitext(file)
            if ext.lower() in binary_extensions:
                skipped_files += 1
                continue
            
            # Get relative path from repo_path
            rel_path = os.path.relpath(file_path, repo_path)
            
            try:
                # First try to detect encoding
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    if not raw_data:
                        file_contents[rel_path] = ""
                        processed_files += 1
                        continue
                        
                    # Try to detect encoding
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] or 'utf-8'
                
                # Then read with detected encoding
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                    file_contents[rel_path] = content
                    processed_files += 1
                    
            except Exception as e:
                print(f"Skipping {rel_path}: {str(e)}")
                skipped_files += 1
    
    print(f"Repository scan complete!")
    print(f"Processed {processed_files} of {total_files} files ({skipped_files} files skipped)")
    
    return file_contents

def save_repo_contents(file_contents, output_file='repo_contents.json'):
    """
    Saves the repository contents dictionary to a JSON file.
    
    Args:
        file_contents: Dictionary with file paths and contents
        output_file: Path to output JSON file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(file_contents, f, indent=2, ensure_ascii=False)
        print(f"Repository contents saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving repository contents: {str(e)}")
        return False

def get_repo_file_tree(repo_path='./repo'):
    """
    Generates a text representation of the repository file tree.
    
    Args:
        repo_path: Path to the local repository folder, defaults to './repo'
        
    Returns:
        String containing formatted file tree
    """
    repo_path = os.path.abspath(repo_path)
    
    if not os.path.exists(repo_path):
        return f"Repository folder not found: {repo_path}"
    
    lines = []
    repo_name = os.path.basename(repo_path)
    lines.append(f"{repo_name}/")
    
    def add_directory(dir_path, prefix=""):
        entries = sorted(os.listdir(dir_path), key=lambda x: (os.path.isfile(os.path.join(dir_path, x)), x))
        
        # Skip hidden entries and node_modules
        entries = [entry for entry in entries if not entry.startswith('.') and entry != 'node_modules']
        
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            entry_path = os.path.join(dir_path, entry)
            
            if is_last:
                branch = "└── "
                next_prefix = prefix + "    "
            else:
                branch = "├── "
                next_prefix = prefix + "│   "
            
            if os.path.isdir(entry_path):
                lines.append(f"{prefix}{branch}{entry}/")
                add_directory(entry_path, next_prefix)
            else:
                lines.append(f"{prefix}{branch}{entry}")
    
    add_directory(repo_path)
    return "\n".join(lines)

if __name__ == "__main__":
    # Default repository path
    repo_path = "./repo"
    
    # Check if repo folder exists
    if not os.path.exists(repo_path):
        print(f"Repository folder not found: {os.path.abspath(repo_path)}")
        print("Please make sure to pull a repository first.")
        exit(1)
    
    # Get repository contents
    file_contents = get_local_repo_contents(repo_path)
    
    # Print some statistics
    print(f"\nTotal files processed: {len(file_contents)}")
    
    # Print the file tree
    print("\nRepository File Tree:")
    print(get_repo_file_tree(repo_path))
    
    # Save contents to a JSON file
    save_option = input("\nDo you want to save the repository contents to a JSON file? (y/n): ").lower()
    if save_option == 'y':
        output_file = input("Enter output file path (default: repo_contents.json): ") or "repo_contents.json"
        save_repo_contents(file_contents, output_file)
    
    # View contents of a specific file
    view_option = input("\nDo you want to view the content of a specific file? (y/n): ").lower()
    if view_option == 'y':
        while True:
            file_path = input("Enter the relative path to the file (or 'exit' to quit): ")
            if file_path.lower() == 'exit':
                break
            if file_path in file_contents:
                print(f"\nContent of {file_path}:\n")
                print("-" * 80)
                print(file_contents[file_path])
                print("-" * 80)
            else:
                print(f"File '{file_path}' not found in repository.")
                print("Available files:")
                for path in sorted(file_contents.keys())[:10]:  # Show first 10 files
                    print(f" - {path}")
                if len(file_contents) > 10:
                    print(f" ... and {len(file_contents) - 10} more files")
