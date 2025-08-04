"""
GitHub Integration Agent for Orion AI Agent System

This agent handles all GitHub-related operations using Composio integration.
"""

import os
import re
import sys
import time
from typing import Dict, List, Optional

from composio import Composio
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class GitHubIntegrationAgent(BaseAgent):
    """
    Agent responsible for GitHub integration operations.

    Capabilities:
    - List repositories
    - Create pull requests
    - Manage GitHub authentication
    - Format GitHub API responses
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the GitHub Integration Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("GitHubIntegration", debug)
        self.openai_client = None
        self.composio_client = None
        self.update_state("authenticated", False)
        self.update_state("repositories", [])
        self.update_state("pull_requests", [])

    def _initialize_clients(self) -> bool:
        """
        Initialize OpenAI and Composio clients.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.openai_client:
                self.openai_client = OpenAI()
                self.log("OpenAI client initialized")

            if not self.composio_client:
                api_key = os.getenv("COMPOSIO_API_KEY")
                if not api_key:
                    self.log("COMPOSIO_API_KEY not found", "error")
                    return False

                self.composio_client = Composio(api_key=api_key)
                self.log("Composio client initialized")

            return True

        except Exception as e:
            self.log(f"Failed to initialize clients: {e}", "error")
            return False

    def check_authentication(self) -> bool:
        """
        Check if authentication is properly set up.

        Returns:
            bool: True if authentication is properly configured, False otherwise
        """

        def _auth_check():
            required_vars = ["COMPOSIO_API_KEY", "USER_ID"]
            missing_vars = []

            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)

            if missing_vars:
                self.log("❌ Missing required environment variables:")
                for var in missing_vars:
                    self.log(f"   - {var}")
                self.log("🔧 To fix this:")
                self.log("1. Copy env_example.txt to .env")
                self.log("2. Fill in your credentials")
                self.log("3. Run: python auth_setup.py")
                self.update_state("authenticated", False)
                return False

            self.update_state("authenticated", True)
            return True

        result = self.execute_with_tracking("check_authentication", _auth_check)
        return result is not None and result

    def list_repositories(self, limit: int = 5) -> Optional[List[Dict]]:
        """
        List repositories from the user's GitHub account using Composio.

        Args:
            limit: Number of repositories to list

        Returns:
            List[Dict]: List of repository information, or None if failed
        """

        def _list_repos_operation():
            if not self.check_authentication():
                return None

            if not self._initialize_clients():
                return None

            user_id = os.getenv("USER_ID")

            # Get GitHub tools
            tools = self.composio_client.tools.get(user_id=user_id, toolkits=["GITHUB"])

            # Create task for listing repositories
            task = f"List {limit} repositories from the user's GitHub account. Include details like name, description, stars, forks, language, and URLs."

            self.log(f"🔍 Fetching {limit} repositories from GitHub account...")

            # Create a chat completion request
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": task}],
                tools=tools,
            )

            # Handle tool calls
            result = self.composio_client.provider.handle_tool_calls(
                user_id=user_id, response=response
            )

            # Format and store results
            formatted_result = self._format_repository_results(result)

            # Update state
            self.update_state("repositories", result)
            self.update_state("last_repo_fetch", time.time())

            return formatted_result

        return self.execute_with_tracking("list_repositories", _list_repos_operation)

    def create_pull_request(
        self,
        repo_url: str,
        title: str,
        body: str,
        branch_name: str = "ai-automated-update",
    ) -> Optional[Dict]:
        """
        Create a GitHub pull request using Composio.

        Args:
            repo_url: GitHub repository URL
            title: Pull request title
            body: Pull request body/description
            branch_name: Source branch name for the PR

        Returns:
            Dict: Pull request information, or None if failed
        """

        def _create_pr_operation():
            if not self.check_authentication():
                return None

            if not self._initialize_clients():
                return None

            user_id = os.getenv("USER_ID")

            # Get GitHub tools
            tools = self.composio_client.tools.get(user_id=user_id, toolkits=["GITHUB"])

            # Extract owner and repo from URL
            repo_parts = repo_url.replace(".git", "").split("/")
            owner = repo_parts[-2]
            repo = repo_parts[-1]

            self.log(f"🚀 Creating pull request for {owner}/{repo}...")
            self.log(f"   📋 Title: {title}")
            self.log(f"   🌿 Branch: {branch_name} → main")

            # Create task for PR creation
            task = f"""Create a pull request in the GitHub repository {owner}/{repo} with the following details:
            - Title: {title}
            - Body: {body}
            - Head branch: {branch_name}
            - Base branch: main
            
            Please use the GitHub API to create this pull request and return the PR details including URL, number, and status."""

            # Create a chat completion request
            response = self.openai_client.chat.completions.create(
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
            result = self.composio_client.provider.handle_tool_calls(
                user_id=user_id, response=response
            )

            # Format and store results
            formatted_result = self._format_pr_results(result)

            # Update state
            pr_info = {
                "repo_url": repo_url,
                "title": title,
                "body": body,
                "branch_name": branch_name,
                "result": result,
                "timestamp": time.time(),
            }

            pull_requests = self.get_state("pull_requests", [])
            pull_requests.append(pr_info)
            self.update_state("pull_requests", pull_requests)

            return formatted_result

        return self.execute_with_tracking("create_pull_request", _create_pr_operation)

    def generate_pr_metadata(self, prompt: str) -> Optional[Dict[str, str]]:
        """Generate branch slug, PR title, and commit message from a prompt using GPT-4o."""

        def _generate():
            if not self.openai_client:
                self.openai_client = OpenAI()
                self.log("OpenAI client initialized")

            system_msg = "Create a concise, human-readable GitHub pull request title."
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=32,
            )

            raw_title = response.choices[0].message["content"].strip()
            slug = re.sub(r"[^a-zA-Z0-9\- ]", "", raw_title).strip().lower()
            slug = re.sub(r"\s+", "-", slug)
            pr_title = f":robot: [orion] {raw_title}"
            return {"slug": slug, "title": pr_title, "commit_message": pr_title}

        return self.execute_with_tracking("generate_pr_metadata", _generate)

    def _format_repository_results(self, result) -> str:
        """
        Format repository listing results in a structured way.

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

    def _format_pr_results(self, result) -> str:
        """
        Format pull request creation results in a structured way.

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
                        formatted_output.append("✅ Pull Request Created Successfully!")
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

    def get_authentication_status(self) -> Dict[str, any]:
        """
        Get the current authentication status.

        Returns:
            Dict: Authentication status information
        """
        return {
            "authenticated": self.get_state("authenticated", False),
            "has_composio_key": bool(os.getenv("COMPOSIO_API_KEY")),
            "has_user_id": bool(os.getenv("USER_ID")),
            "clients_initialized": bool(self.openai_client and self.composio_client),
        }

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the GitHub Integration Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "check_auth": self.check_authentication,
            "list_repos": self.list_repositories,
            "create_pr": self.create_pull_request,
            "auth_status": self.get_authentication_status,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
