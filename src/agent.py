import os
import subprocess
from typing import Optional
from pprint import pprint
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI  # Correct import
from langchain_core.prompts import ChatPromptTemplate  # Correct import
from langchain_core.output_parsers import StrOutputParser
from composio import Composio  # Updated Composio import
from openai import OpenAI

# Load environment variables
load_dotenv()


def clone_repo(repo_url: str, clone_path: str) -> None:
    """Clone a GitHub repo to `clone_path` or use existing repo if it exists."""
    if os.path.exists(clone_path):
        print(f"Repository already exists at {clone_path}")
        # Check if it's a valid git repository
        try:
            original_dir = os.getcwd()
            os.chdir(clone_path)
            subprocess.run(["git", "status"], check=True, capture_output=True)
            print("✅ Using existing repository")
            # Fetch latest changes
            print("🔄 Fetching latest changes...")
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            # Switch to main/master branch
            try:
                subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(["git", "checkout", "master"], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print("⚠️ Could not switch to main/master branch, staying on current branch")
            os.chdir(original_dir)
        except subprocess.CalledProcessError:
            print(f"⚠️ Directory exists but is not a valid git repository. Removing and cloning fresh...")
            import shutil
            shutil.rmtree(clone_path)
            print(f"Cloning repository {repo_url} to {clone_path}")
            subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        return
    
    print(f"Cloning repository {repo_url} to {clone_path}")
    subprocess.run(["git", "clone", repo_url, clone_path], check=True)


def get_unique_branch_name(base_name: str, repo_path: str) -> str:
    """Generate a unique branch name that doesn't conflict with existing branches.
    
    Args:
        base_name: The base name for the branch
        repo_path: Path to the git repository
        
    Returns:
        str: A unique branch name
    """
    try:
        # Get list of all branches (local and remote)
        result = subprocess.run(
            ["git", "branch", "-a"], 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=repo_path
        )
        existing_branches = set()
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('*'):
                # Remove 'remotes/origin/' prefix if present
                branch_name = line.replace('remotes/origin/', '').strip()
                if branch_name and branch_name != 'HEAD':
                    existing_branches.add(branch_name)
        
        # Check if base_name is available
        if base_name not in existing_branches:
            return base_name
        
        # Generate unique name with counter
        counter = 1
        while f"{base_name}-{counter}" in existing_branches:
            counter += 1
        
        return f"{base_name}-{counter}"
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Could not get branch list: {e}")
        # Fallback: use timestamp
        import time
        timestamp = int(time.time())
        return f"{base_name}-{timestamp}"


def generate_code_changes(prompt: str, repo_path: str) -> str:
    """Generate code changes for the repository based on the prompt."""
    # Use ChatOpenAI instead of deprecated OpenAI
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Specify the model explicitly
        temperature=0.1
    )
    
    # Create proper prompt template
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI engineer. Analyze the repository and provide specific code implementations. "
                  "For each file you want to create or modify, provide the content in the following format:\n"
                  "FILE: filename.py\n"
                  "```python\n"
                  "# Complete file content here\n"
                  "```\n"
                  "Be sure to include all necessary imports and complete, runnable code."),
        ("user", "Repository path: {repo_path}\nTask: {prompt}\n\n"
                 "Please provide the complete code files needed to accomplish this task. "
                 "Include proper imports, error handling, and documentation.")
    ])
    
    # Use the modern approach instead of deprecated LLMChain
    chain = template | llm | StrOutputParser()
    
    return chain.invoke({"prompt": prompt, "repo_path": repo_path})


def make_code_changes(repo_path: str, changes_description: str) -> None:
    """Make the actual code changes to the repository."""
    print(f"Implementing AI-generated changes in: {repo_path}")
    
    # Parse the changes_description to extract file names and content
    import re
    
    # Find all FILE: patterns followed by code blocks
    file_pattern = r'FILE:\s*([^\n]+)\n```(?:python)?\n(.*?)```'
    matches = re.findall(file_pattern, changes_description, re.DOTALL)
    
    if not matches:
        # Fallback: if no structured format, create a default Python script
        print("No structured file format found. Creating default Python script...")
        script_content = extract_python_code_from_text(changes_description)
        if script_content:
            filename = "clip_script.py"
            filepath = os.path.join(repo_path, filename)
            with open(filepath, "w") as f:
                f.write(script_content)
            print(f"✅ Created: {filename}")
        else:
            # If no Python code found, create documentation
            changes_file = os.path.join(repo_path, "AI_SUGGESTED_CHANGES.md")
            with open(changes_file, "w") as f:
                f.write("# AI Suggested Changes\n\n")
                f.write(changes_description)
            print(f"📝 Changes documented in: AI_SUGGESTED_CHANGES.md")
        return
    
    # Create each file found in the structured format
    created_files = []
    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()
        
        # Ensure the filename has proper extension
        if not filename.endswith('.py') and not '.' in filename:
            filename += '.py'
        
        filepath = os.path.join(repo_path, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            created_files.append(filename)
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    if created_files:
        print(f"\n🎉 Successfully created {len(created_files)} file(s): {', '.join(created_files)}")
    else:
        print("⚠️ No files were created")


def extract_python_code_from_text(text: str) -> str:
    """Extract Python code from text, looking for code blocks or Python-like content."""
    import re
    
    # Look for Python code blocks
    python_blocks = re.findall(r'```python\n(.*?)```', text, re.DOTALL)
    if python_blocks:
        return python_blocks[0].strip()
    
    # Look for any code blocks
    code_blocks = re.findall(r'```\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        # Check if it looks like Python code
        for block in code_blocks:
            if any(keyword in block for keyword in ['import', 'def ', 'class ', 'from ', 'print(']):
                return block.strip()
    
    # If no code blocks, try to extract Python-like content
    lines = text.split('\n')
    python_lines = []
    in_code_section = False
    
    for line in lines:
        # Start collecting if we see Python keywords
        if any(keyword in line for keyword in ['import ', 'from ', 'def ', 'class ', 'if __name__']):
            in_code_section = True
        
        if in_code_section:
            python_lines.append(line)
    
    if python_lines:
        code = '\n'.join(python_lines)
        # Basic validation - should have imports or function definitions
        if 'import' in code or 'def ' in code:
            return code
    
    return ""


def format_repository_results(result):
    """Format repository listing results in a structured way.
    
    Args:
        result: The raw result from Composio tool call
        
    Returns:
        str: Formatted output
    """
    try:
        if not result or not isinstance(result, list):
            return "No repositories found or invalid result format."
        
        formatted_output = []
        formatted_output.append("📚 GitHub Repositories")
        formatted_output.append("=" * 50)
        
        for item in result:
            if 'data' in item and 'details' in item['data']:
                repos = item['data']['details']
                if isinstance(repos, list):
                    for i, repo in enumerate(repos, 1):
                        if isinstance(repo, dict):
                            formatted_output.append(f"\n{i}. {repo.get('name', 'Unknown')}")
                            formatted_output.append(f"   🔗 URL: {repo.get('html_url', 'N/A')}")
                            formatted_output.append(f"   📝 Description: {repo.get('description', 'No description')}")
                            formatted_output.append(f"   🌟 Stars: {repo.get('stargazers_count', 0)}")
                            formatted_output.append(f"   🍴 Forks: {repo.get('forks_count', 0)}")
                            formatted_output.append(f"   📅 Updated: {repo.get('updated_at', 'Unknown')}")
                            formatted_output.append(f"   🔒 Private: {'Yes' if repo.get('private', False) else 'No'}")
                            formatted_output.append(f"   📋 Language: {repo.get('language', 'Not specified')}")
                            
                            # Add clone URL
                            clone_url = repo.get('clone_url', repo.get('git_url', 'N/A'))
                            formatted_output.append(f"   📥 Clone: {clone_url}")
                            
                            # Add default branch
                            default_branch = repo.get('default_branch', 'main')
                            formatted_output.append(f"   🌿 Default branch: {default_branch}")
                            
                            formatted_output.append("")  # Empty line for spacing
        
        return "\n".join(formatted_output)
        
    except Exception as e:
        return f"Error formatting results: {e}\nRaw result: {result}"


def format_pr_results(result):
    """Format pull request creation results in a structured way.
    
    Args:
        result: The raw result from Composio tool call
        
    Returns:
        str: Formatted output
    """
    try:
        if not result or not isinstance(result, list):
            return "No PR creation result or invalid result format."
        
        formatted_output = []
        formatted_output.append("🚀 Pull Request Creation Result")
        formatted_output.append("=" * 50)
        
        for item in result:
            if 'data' in item:
                pr_data = item['data']
                if isinstance(pr_data, dict):
                    formatted_output.append(f"✅ Pull Request Created Successfully!")
                    formatted_output.append(f"   📋 Title: {pr_data.get('title', 'N/A')}")
                    formatted_output.append(f"   🔗 URL: {pr_data.get('html_url', 'N/A')}")
                    formatted_output.append(f"   🔢 PR Number: #{pr_data.get('number', 'N/A')}")
                    formatted_output.append(f"   📝 State: {pr_data.get('state', 'N/A')}")
                    formatted_output.append(f"   👤 Author: {pr_data.get('user', {}).get('login', 'N/A')}")
                    formatted_output.append(f"   🌿 Base: {pr_data.get('base', {}).get('ref', 'N/A')}")
                    formatted_output.append(f"   🌿 Head: {pr_data.get('head', {}).get('ref', 'N/A')}")
                    formatted_output.append(f"   📅 Created: {pr_data.get('created_at', 'N/A')}")
                    
                    # Add description if available
                    if pr_data.get('body'):
                        formatted_output.append(f"   📄 Description: {pr_data.get('body')[:100]}...")
        
        return "\n".join(formatted_output)
        
    except Exception as e:
        return f"Error formatting PR results: {e}\nRaw result: {result}"


def check_authentication_setup():
    """Check if authentication is properly set up.
    
    Returns:
        bool: True if authentication is properly configured, False otherwise
    """
    required_vars = ["COMPOSIO_API_KEY", "USER_ID"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n🔧 To fix this:")
        print("1. Copy env_example.txt to .env")
        print("2. Fill in your credentials")
        print("3. Run: python auth_setup.py")
        return False
    
    return True


def list_repositories_with_composio(limit: int = 5) -> None:
    """List repositories from the user's GitHub account using Composio.
    
    Args:
        limit: Number of repositories to list (default: 5)
    """
    # Check authentication setup first
    if not check_authentication_setup():
        return
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAI()
        
        # Initialize Composio with API key
        composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))
        
        # User ID must be a valid UUID format
        user_id = os.getenv("USER_ID")
        
        # Get GitHub tools
        tools = composio.tools.get(user_id=user_id, toolkits=["GITHUB"])
        
        # Create task for listing repositories
        task = f"List {limit} repositories from the user's GitHub account. Include details like name, description, stars, forks, language, and URLs."
        
        print(f"🔍 Fetching {limit} repositories from your GitHub account...")
        
        # Create a chat completion request
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": task,
                },
            ],
            tools=tools,
        )
        
        # Handle tool calls
        result = composio.provider.handle_tool_calls(user_id=user_id, response=response)
        
        # Format and display the results
        formatted_result = format_repository_results(result)
        print(formatted_result)
        
        # Optional: Show raw data if in debug mode
        if os.getenv("DEBUG") == "true":
            print("\n" + "="*50)
            print("🔧 DEBUG: Raw Response")
            print("="*50)
            print(f"OpenAI Response: {response}")
            print(f"\nTool Call Result: {result}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error listing repositories with Composio: {e}")
        
        if "No connected account found" in error_msg:
            print("\n🔧 GitHub account not connected. To fix this:")
            print("1. Run: python auth_setup.py")
            print("2. Follow the authentication flow")
            print("3. Make sure GITHUB_AUTH_CONFIG_ID is set in your .env file")
        else:
            print("\n🔧 Make sure you have:")
            print("1. Set COMPOSIO_API_KEY environment variable")
            print("2. Set USER_ID environment variable (must be a valid UUID)")
            print("3. Connected your GitHub account to Composio")
            print("4. Run: python auth_setup.py if you haven't already")


def create_pr_with_composio(repo_url: str, title: str, body: str, branch_name: str = "ai-automated-update") -> None:
    """Create a GitHub pull request using Composio.
    
    Args:
        repo_url: GitHub repository URL
        title: Pull request title
        body: Pull request body/description
        branch_name: Source branch name for the PR
    """
    # Check authentication setup first
    if not check_authentication_setup():
        return
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAI()
        
        # Initialize Composio with API key
        composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))
        
        # User ID must be a valid UUID format
        user_id = os.getenv("USER_ID")
        
        # Get GitHub tools
        tools = composio.tools.get(user_id=user_id, toolkits=["GITHUB"])
        
        # Extract owner and repo from URL
        # Example: https://github.com/owner/repo.git -> owner/repo
        repo_parts = repo_url.replace('.git', '').split('/')
        owner = repo_parts[-2]
        repo = repo_parts[-1]
        
        print(f"🚀 Creating pull request for {owner}/{repo}...")
        print(f"   📋 Title: {title}")
        print(f"   🌿 Branch: {branch_name} → main")
        
        # Create task for PR creation
        task = f"""Create a pull request in the GitHub repository {owner}/{repo} with the following details:
        - Title: {title}
        - Body: {body}
        - Head branch: {branch_name}
        - Base branch: main
        
        Please use the GitHub API to create this pull request and return the PR details including URL, number, and status."""
        
        # Create a chat completion request
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that creates GitHub pull requests using the available GitHub tools."
                },
                {
                    "role": "user", 
                    "content": task
                }
            ],
            tools=tools,
        )
        
        # Handle tool calls
        result = composio.provider.handle_tool_calls(user_id=user_id, response=response)
        
        # Format and display the results
        formatted_result = format_pr_results(result)
        print(formatted_result)
        
        # Optional: Show raw data if in debug mode
        if os.getenv("DEBUG") == "true":
            print("\n" + "="*50)
            print("🔧 DEBUG: Raw Response")
            print("="*50)
            print(f"OpenAI Response: {response}")
            print(f"\nTool Call Result: {result}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error creating pull request with Composio: {e}")
        
        if "No connected account found" in error_msg:
            print("\n🔧 GitHub account not connected. To fix this:")
            print("1. Run: python auth_setup.py")
            print("2. Follow the authentication flow")
            print("3. Make sure GITHUB_AUTH_CONFIG_ID is set in your .env file")
        else:
            print("You can manually create the PR on GitHub with the following details:")
            print(f"Title: {title}")
            print(f"Body: {body}")
            print(f"Branch: {branch_name}")
            print(f"Repository: {repo_url}")
            print("\n🔧 Make sure you have:")
            print("1. Set COMPOSIO_API_KEY environment variable")
            print("2. Set USER_ID environment variable (must be a valid UUID)")
            print("3. Connected your GitHub account to Composio")
            print("4. Have proper permissions to create PRs in the target repository")
            print("5. Run: python auth_setup.py if you haven't already")


def run(repo_url: str, user_prompt: str, workdir: Optional[str] = None) -> None:
    """Main workflow for the agent."""
    if workdir is None:
        workdir = "repo"
    
    # Extract repo name from URL for branch naming and directory naming
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    base_branch_name = f"ai-update-{repo_name}"
    
    # Create the full path for the repository
    repo_path = os.path.join(workdir, repo_name)
    
    try:
        print(f"Starting AI agent workflow for: {repo_url}")
        print(f"Task: {user_prompt}")
        
        # Clone repository to the specific repo directory
        clone_repo(repo_url, repo_path)
        
        # Change to repo directory
        original_dir = os.getcwd()
        os.chdir(repo_path)
        
        # Check if we're in a git repository
        try:
            subprocess.run(["git", "status"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Error: Not a valid git repository")
            return
        
        # Generate unique branch name
        branch_name = get_unique_branch_name(base_branch_name, repo_path)
        print(f"Generated unique branch name: {branch_name}")
        
        # Create new branch
        print(f"Creating new branch: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        
        # Generate code changes using AI
        print("Generating code changes using AI...")
        changes = generate_code_changes(user_prompt, repo_path)
        
        # Make the code changes
        make_code_changes(".", changes)
        
        # Stage and commit changes
        print("Staging and committing changes...")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"AI-generated changes: {user_prompt}"], check=True)
        
        # Push branch (this might fail if you don't have push access)
        try:
            print(f"Pushing branch: {branch_name}")
            subprocess.run(["git", "push", "origin", branch_name], check=True)
            
            # Create pull request using Composio
            print("Creating pull request...")
            create_pr_with_composio(
                repo_url, 
                f"AI-generated update: {user_prompt}", 
                f"This PR contains AI-generated changes for: {user_prompt}\n\nChanges:\n{changes}",
                branch_name
            )
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to push branch. Error: {e}")
            print("You may need to:")
            print("1. Fork the repository first")
            print("2. Ensure you have push access")
            print("3. Set up authentication (SSH keys or personal access token)")
        
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        print("Make sure you have git installed and the repository URL is correct")
    except Exception as e:
        print(f"Error in workflow: {e}")
    finally:
        # Return to original directory
        os.chdir(original_dir)
        
def show_help_summary():
    """Show a helpful summary of available commands."""
    print("\n" + "="*60)
    print("🚀 Orion AI Agent - Available Commands")
    print("="*60)
    print()
    print("📋 Repository Management:")
    print("  python src/agent.py --list-repos                    # List your repositories")
    print("  python src/agent.py --list-repos --repo-limit 10    # List 10 repositories")
    print()
    print("🔧 Authentication:")
    print("  python src/agent.py --setup-auth                    # Setup GitHub authentication")
    print("  python auth_setup.py                                # Direct auth setup")
    print()
    print("🤖 AI Agent Operations:")
    print("  python src/agent.py --repo-url <url> --prompt <task>")
    print("  python src/agent.py --repo-url https://github.com/owner/repo \\")
    print("                      --prompt 'Add authentication to the API'")
    print()
    print("🔍 Debug Mode:")
    print("  python src/agent.py --list-repos --debug            # Show raw API responses")
    print()
    print("📚 Setup & Help:")
    print("  python setup_guide.py                               # Initial setup guide")
    print("  python src/agent.py --help                          # Show all options")
    print()
    print("🌐 Useful Links:")
    print("  • Composio Dashboard: https://app.composio.dev/")
    print("  • OpenAI API Keys: https://platform.openai.com/api-keys")
    print("  • GitHub: https://github.com/")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Orion AI agent")
    parser.add_argument("--list-repos", action="store_true", help="List repositories from your GitHub account")
    parser.add_argument("--repo-url", help="GitHub repository URL", default="https://github.com/ishandutta0098/open-clip")
    parser.add_argument("--prompt", help="Instruction for the AI agent", default="Create a python script to use clip model from transformers library")
    parser.add_argument("--workdir", help="Working directory for cloning", default="/Users/ishandutta/Documents/code")
    parser.add_argument("--repo-limit", type=int, default=5, help="Number of repositories to list (default: 5)")
    parser.add_argument("--setup-auth", action="store_true", help="Run authentication setup")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to show raw API responses")
    parser.add_argument("--show-commands", action="store_true", help="Show available commands and examples")
    args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        os.environ["DEBUG"] = "true"
        print("🔧 Debug mode enabled - raw API responses will be shown")
    
    if args.show_commands:
        show_help_summary()
    elif args.setup_auth:
        print("🔧 Running authentication setup...")
        import subprocess
        subprocess.run(["python", "auth_setup.py"])
    elif args.list_repos:
        print("📚 Listing repositories from your GitHub account...")
        list_repositories_with_composio(args.repo_limit)
        print("\n💡 Tip: Use --debug flag to see raw API responses")
        print("💡 Tip: Run 'python agent.py --show-commands' to see all available commands")
    else:
        # Check authentication before running the main workflow
        if not check_authentication_setup():
            print("\n💡 Tip: Run 'python agent.py --setup-auth' to set up authentication")
            print("💡 Tip: Run 'python agent.py --show-commands' to see all available commands")
            exit(1)
        
        print(f"🤖 Running AI agent on repository: {args.repo_url}")
        print(f"📝 Task: {args.prompt}")
        run(args.repo_url, args.prompt, args.workdir)