import os

from composio import Composio
from openai import OpenAI


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
            if "data" in item and "details" in item["data"]:
                repos = item["data"]["details"]
                if isinstance(repos, list):
                    for i, repo in enumerate(repos, 1):
                        if isinstance(repo, dict):
                            formatted_output.append(
                                f"\n{i}. {repo.get('name', 'Unknown')}"
                            )
                            formatted_output.append(
                                f"   🔗 URL: {repo.get('html_url', 'N/A')}"
                            )
                            formatted_output.append(
                                f"   📝 Description: {repo.get('description', 'No description')}"
                            )
                            formatted_output.append(
                                f"   🌟 Stars: {repo.get('stargazers_count', 0)}"
                            )
                            formatted_output.append(
                                f"   🍴 Forks: {repo.get('forks_count', 0)}"
                            )
                            formatted_output.append(
                                f"   📅 Updated: {repo.get('updated_at', 'Unknown')}"
                            )
                            formatted_output.append(
                                f"   🔒 Private: {'Yes' if repo.get('private', False) else 'No'}"
                            )
                            formatted_output.append(
                                f"   📋 Language: {repo.get('language', 'Not specified')}"
                            )

                            # Add clone URL
                            clone_url = repo.get(
                                "clone_url", repo.get("git_url", "N/A")
                            )
                            formatted_output.append(f"   📥 Clone: {clone_url}")

                            # Add default branch
                            default_branch = repo.get("default_branch", "main")
                            formatted_output.append(
                                f"   🌿 Default branch: {default_branch}"
                            )

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
            if "data" in item:
                pr_data = item["data"]
                if isinstance(pr_data, dict):
                    formatted_output.append(f"✅ Pull Request Created Successfully!")
                    formatted_output.append(
                        f"   📋 Title: {pr_data.get('title', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   🔗 URL: {pr_data.get('html_url', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   🔢 PR Number: #{pr_data.get('number', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   📝 State: {pr_data.get('state', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   👤 Author: {pr_data.get('user', {}).get('login', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   🌿 Base: {pr_data.get('base', {}).get('ref', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   🌿 Head: {pr_data.get('head', {}).get('ref', 'N/A')}"
                    )
                    formatted_output.append(
                        f"   📅 Created: {pr_data.get('created_at', 'N/A')}"
                    )

                    # Add description if available
                    if pr_data.get("body"):
                        formatted_output.append(
                            f"   📄 Description: {pr_data.get('body')[:100]}..."
                        )

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
            print("\n" + "=" * 50)
            print("🔧 DEBUG: Raw Response")
            print("=" * 50)
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


def create_pr_with_composio(
    repo_url: str, title: str, body: str, branch_name: str = "ai-automated-update"
) -> None:
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
        repo_parts = repo_url.replace(".git", "").split("/")
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
                    "content": "You are a helpful assistant that creates GitHub pull requests using the available GitHub tools.",
                },
                {"role": "user", "content": task},
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
            print("\n" + "=" * 50)
            print("🔧 DEBUG: Raw Response")
            print("=" * 50)
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
            print(
                "You can manually create the PR on GitHub with the following details:"
            )
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
