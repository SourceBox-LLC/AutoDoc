#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def clone_github_repo(github_url):
    """
    Clones a public GitHub repository to a folder named 'repo'
    
    Args:
        github_url (str): URL of the GitHub repository to clone
    """
    # Ensure the repo folder is empty or doesn't exist
    repo_dir = "repo"
    
    if os.path.exists(repo_dir):
        print(f"Removing existing '{repo_dir}' directory...")
        shutil.rmtree(repo_dir)
    
    try:
        # Clone the repository
        print(f"Cloning {github_url} into '{repo_dir}'...")
        subprocess.run(["git", "clone", github_url, repo_dir], check=True)
        print("Repository cloned successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to clone repository. Make sure the URL is correct and you have git installed.")
        print(f"Command returned: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main(github_url=None):
    """Main function that can be called by other modules or run directly"""
    if github_url is None:
        print("Usage: python pull_repo.py <github_repository_url>")
        print("Example: python pull_repo.py https://github.com/username/repository.git")
        return False
    
    clone_github_repo(github_url)
    return True

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
