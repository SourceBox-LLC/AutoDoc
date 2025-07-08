import os
import argparse
import asyncio
import glob
from pathlib import Path
from ai import get_ai_response, ARGS, SYSTEM

def scan_repository(repo_path, max_files=50, ignored_dirs=('docs', '.git', '__pycache__', 'venv', '.venv', 'node_modules')):
    """
    Scan repository and extract code content from files.
    
    Args:
        repo_path: Path to the repository
        max_files: Maximum number of files to process (to prevent token limits)
        ignored_dirs: Directories to ignore
    
    Returns:
        dict: A dictionary with file structure and content
    """
    repo_structure = {
        'files': {},
        'summary': {},
        'file_count': 0
    }
    
    # Get all non-binary files, sorted by importance
    file_extensions = [
        '*.py', '*.js', '*.jsx', '*.ts', '*.tsx', # Code files first
        '*.html', '*.css', '*.scss', '*.json',    # Web/config files
        '*.md', '*.txt', 'README*'                # Documentation
    ]
    
    # Track files we've already found to avoid duplicates
    found_files = set()
    
    # First, check if there's a README file and prioritize it
    readme_files = glob.glob(f"{repo_path}/README*")
    for readme in readme_files:
        if repo_structure['file_count'] >= max_files:
            break
            
        rel_path = os.path.relpath(readme, repo_path)
        try:
            with open(readme, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                repo_structure['files'][rel_path] = content
                repo_structure['file_count'] += 1
                found_files.add(os.path.abspath(readme))
        except Exception as e:
            repo_structure['summary'][rel_path] = f"Error reading file: {str(e)}"
    
    # Then look for specific extensions in priority order
    for ext in file_extensions:
        if repo_structure['file_count'] >= max_files:
            break
            
        for filepath in glob.glob(f"{repo_path}/**/{ext}", recursive=True):
            # Skip files in ignored directories
            if any(ignored in filepath for ignored in ignored_dirs):
                continue
                
            # Skip files we already processed
            abs_path = os.path.abspath(filepath)
            if abs_path in found_files:
                continue
                
            if repo_structure['file_count'] >= max_files:
                break
                
            rel_path = os.path.relpath(filepath, repo_path)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    repo_structure['files'][rel_path] = content
                    repo_structure['file_count'] += 1
                    found_files.add(abs_path)
            except Exception as e:
                repo_structure['summary'][rel_path] = f"Error reading file: {str(e)}"
    
    # Add information about total files in repo
    all_files = set()
    for ext in file_extensions:
        for filepath in glob.glob(f"{repo_path}/**/{ext}", recursive=True):
            if not any(ignored in filepath for ignored in ignored_dirs):
                all_files.add(filepath)
    
    repo_structure['total_files'] = len(all_files)
    repo_structure['analyzed_percentage'] = (repo_structure['file_count'] / len(all_files) * 100) if all_files else 100
    
    return repo_structure

def format_repository_context(repo_data):
    """Format repository content into a readable context for the AI."""
    context = "REPOSITORY OVERVIEW:\n\n"
    
    # Add metadata
    context += f"Total files: {repo_data['total_files']}\n"
    context += f"Files analyzed: {repo_data['file_count']} ({repo_data['analyzed_percentage']:.1f}%)\n\n"
    
    # Add file listing
    context += "FILES IN REPOSITORY:\n"
    for filename in repo_data['files'].keys():
        context += f"- {filename}\n"
    context += "\n"
    
    # Add file content
    context += "FILE CONTENTS:\n\n"
    for filename, content in repo_data['files'].items():
        context += f"--- BEGIN {filename} ---\n"
        # Limit each file to ~5000 chars to prevent token overflow
        if len(content) > 5000:
            context += content[:5000] + "\n... (file truncated due to size)\n"
        else:
            context += content + "\n"
        context += f"--- END {filename} ---\n\n"
    
    return context

# advanced doc generation
async def create_docs_dir(api_overview=False, examples=False, guides=False, output_dir="docs", target_repo_path=None):
    """Create a docs directory if it doesn't exist and generate AI-powered documentation.
    
    Args:
        api_overview: If True, generate API documentation
        examples: If True, generate examples documentation
        guides: If True, generate guides documentation
        output_dir: Directory where documentation will be stored
        target_repo_path: Path to the repository to document (different from the Lightning MD repo)
    """
    # If target_repo_path is not provided, use the current directory
    if target_repo_path is None:
        target_repo_path = "."
        print("Warning: No target repository specified. Using current directory.")
    
    # Verify target repo exists
    if not os.path.isdir(target_repo_path):
        print(f"Error: Target repository path '{target_repo_path}' is not a valid directory.")
        return
        
    # Create the main docs directory first
    os.makedirs(output_dir, exist_ok=True)
    
    # Scan repository for actual content
    print(f"Scanning target repository: {target_repo_path}...")
    repo_data = scan_repository(target_repo_path)
    repo_context = format_repository_context(repo_data)
    print(f"Analyzed {repo_data['file_count']} files from the target repository")
    
    # Generate index page with AI
    print("Generating index.md...")
    index_prompt = f"""Generate a main index page for documentation of this repository.
    Use the following repository content as context for generating accurate documentation:
    
    {repo_context}
    
    The index page should serve as a landing page that introduces the project and links to the different documentation sections.
    Include a brief overview of the project and its purpose based on the actual code and structure."""
    
    index_content = await get_ai_response(index_prompt, SYSTEM, ARGS)
    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, "w") as f:
        f.write(index_content)
    print(f"Generated {index_path}")
    
    if api_overview:
        api_dir = os.path.join(output_dir, "api")
        os.makedirs(api_dir, exist_ok=True)
        
        # Generate API overview with AI using actual code content
        print("Generating API documentation...")
        api_prompt = f"""Generate comprehensive API documentation overview for this repository.
        Use the following repository content as context for generating accurate documentation:
        
        {repo_context}
        
        Include information about the main modules, classes, and functions found in the actual code.
        Focus on explaining how to use the API, parameters, return values, and provide code examples where appropriate.
        Organize the content with clear headings and sections."""
        
        api_content = await get_ai_response(api_prompt, SYSTEM, ARGS)
        api_path = os.path.join(api_dir, "overview.md")
        with open(api_path, "w") as f:
            f.write(api_content)
        print(f"Generated {api_path}")

    if examples:
        examples_dir = os.path.join(output_dir, "examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        # Generate examples with AI using actual code content
        print("Generating examples...")
        examples_prompt = f"""Generate practical code examples for this repository.
        Use the following repository content as context:
        
        {repo_context}
        
        Based on the ACTUAL code in the repository, include real-world usage scenarios showing how to use the main features.
        Make sure examples are complete, well-commented, and demonstrate best practices.
        Start with simple examples and progress to more complex ones.
        The examples should be directly based on the actual code structure and API found in the repository."""
        
        examples_content = await get_ai_response(examples_prompt, SYSTEM, ARGS)
        examples_path = os.path.join(examples_dir, "overview.md")
        with open(examples_path, "w") as f:
            f.write(examples_content)
        print(f"Generated {examples_path}")
    
    if guides:
        guides_dir = os.path.join(output_dir, "guides")
        os.makedirs(guides_dir, exist_ok=True)
        
        # Generate guides with AI using actual code content
        print("Generating guides...")
        guides_prompt = f"""Generate comprehensive guides for this repository.
        Use the following repository content as context:
        
        {repo_context}
        
        Based on the ACTUAL code in the repository, create detailed tutorials that walk users through different aspects of using the project.
        Include step-by-step instructions, explanations of concepts, and best practices.
        Focus on common use cases and potential challenges users might face based on the actual code implementation."""
        
        guides_content = await get_ai_response(guides_prompt, SYSTEM, ARGS)
        guides_path = os.path.join(guides_dir, "overview.md")
        with open(guides_path, "w") as f:
            f.write(guides_content)
        print(f"Generated {guides_path}")


# This function is no longer needed as we're not using command-line arguments
# Keeping the stub for compatibility with any existing code
def parse_script_args():
    """This function is deprecated. Used to parse command-line arguments."""
    pass

# Function to be called from app.py to generate documentation
def generate_documentation(docs_options=None, target_repo="repo", output_dir="docs"):
    """
    Generate documentation based on selected options.
    
    Args:
        docs_options: List of doc types to generate ("API Reference", "Examples", "Guides")
        target_repo: Path to the repository to document
        output_dir: Directory where documentation will be saved
    """
    # Convert friendly option names to function parameters
    generate_api = "API Reference" in docs_options if docs_options else True
    generate_examples = "Examples" in docs_options if docs_options else True
    generate_guides = "Guides" in docs_options if docs_options else True
    
    # If docs_options is empty or None, generate all by default
    if not docs_options:
        generate_api = generate_examples = generate_guides = True
    
    print(f"Generating documentation for repository: {target_repo}")
    print(f"Output will be saved to: {output_dir}")
    print(f"Generating: " + 
          ("API Reference, " if generate_api else "") +
          ("Examples, " if generate_examples else "") +
          ("Guides" if generate_guides else ""))
    
    # Run the async function using asyncio
    return asyncio.run(create_docs_dir(
        api_overview=generate_api,
        examples=generate_examples,
        guides=generate_guides,
        output_dir=output_dir,
        target_repo_path=target_repo
    ))


# Keep a simplified version of the main execution for testing purposes
if __name__ == "__main__":
    # Default test execution with all docs enabled
    generate_documentation(docs_options=["API Reference", "Examples", "Guides"], target_repo="repo", output_dir="docs")