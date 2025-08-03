"""
Workflow Orchestrator Agent for Orion AI Agent System

This agent coordinates all other agents and manages the complete workflow.
"""

import json
import os
import re
import sys
import time
from typing import Dict, List, Optional

from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent

from .ai_generator_agent import AIGeneratorAgent
from .code_tester_agent import CodeTesterAgent
from .environment_manager_agent import EnvironmentManagerAgent
from .git_operations_agent import GitOperationsAgent
from .github_integration_agent import GitHubIntegrationAgent


class WorkflowOrchestratorAgent(BaseAgent):
    """
    Main orchestrator agent that coordinates all other agents.

    Capabilities:
    - Coordinate multi-agent workflows
    - Manage agent communication
    - Handle workflow state and progress
    - Provide comprehensive reporting
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Workflow Orchestrator Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("WorkflowOrchestrator", debug)

        # Initialize all sub-agents
        self.git_agent = GitOperationsAgent(debug=debug)
        self.ai_agent = AIGeneratorAgent(debug=debug)
        self.github_agent = GitHubIntegrationAgent(debug=debug)
        self.env_agent = EnvironmentManagerAgent(debug=debug)
        self.test_agent = CodeTesterAgent(debug=debug)
        self.openai_client = None

        # Workflow state
        self.update_state("workflow_sessions", [])
        self.update_state("current_session", None)
        self.update_state("agents_status", {})

        self.log("🚀 Workflow Orchestrator Agent initialized with all sub-agents")

    def run_complete_workflow(
        self,
        repo_url: str,
        user_prompt: str,
        workdir: Optional[str] = None,
        enable_testing: bool = True,
        create_venv: bool = True,
        strict_testing: bool = False,
        commit_changes: bool = False,
        create_pr: bool = False,
    ) -> Dict[str, any]:
        """
        Run the complete AI agent workflow.

        Args:
            repo_url: GitHub repository URL
            user_prompt: Task description for the AI
            workdir: Working directory for cloning
            enable_testing: Whether to test the generated code
            create_venv: Whether to create a virtual environment
            strict_testing: Whether to abort on test failures
            commit_changes: Whether to commit the changes
            create_pr: Whether to create a pull request

        Returns:
            Dict: Workflow results and summary
        """

        def _workflow_operation():
            # Initialize workflow session
            session = self._initialize_workflow_session(
                repo_url,
                user_prompt,
                workdir,
                enable_testing,
                create_venv,
                strict_testing,
                commit_changes,
                create_pr,
            )

            try:
                # Phase 1: Repository Setup
                self.log("=" * 60)
                self.log("🔄 PHASE 1: Repository Setup")
                self.log("=" * 60)

                repo_path = self._setup_repository(repo_url, workdir, session, user_prompt)
                if not repo_path:
                    session["status"] = "failed"
                    session["error"] = "Repository setup failed"
                    return session

                # Phase 2: AI Code Generation
                self.log("=" * 60)
                self.log("🤖 PHASE 2: AI Code Generation")
                self.log("=" * 60)

                generated_code, created_files = self._generate_code(
                    user_prompt, repo_path, session
                )
                if not generated_code:
                    session["status"] = "failed"
                    session["error"] = "Code generation failed"
                    return session

                # Phase 3: Environment and Testing (if enabled)
                if enable_testing and create_venv:
                    self.log("=" * 60)
                    self.log("🧪 PHASE 3: Environment Setup and Testing")
                    self.log("=" * 60)

                    test_passed = self._setup_environment_and_test(
                        repo_path, created_files, strict_testing, session
                    )
                    if not test_passed and strict_testing:
                        session["status"] = "failed"
                        session["error"] = "Tests failed in strict mode"
                        return session

                # Phase 4: Git Operations (if enabled)
                if commit_changes:
                    self.log("=" * 60)
                    self.log("📝 PHASE 4: Git Operations")
                    self.log("=" * 60)

                    commit_success = self._commit_and_push(
                        repo_path, user_prompt, create_pr, repo_url, session
                    )
                    if not commit_success:
                        session["status"] = "failed"
                        session["error"] = "Git operations failed"
                        return session

                # Workflow completed successfully
                session["status"] = "completed"
                session["end_time"] = time.time()
                session["duration"] = session["end_time"] - session["start_time"]

                self.log("=" * 60)
                self.log("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
                self.log("=" * 60)

                return session

            except Exception as e:
                session["status"] = "failed"
                session["error"] = str(e)
                session["end_time"] = time.time()
                self.log(f"❌ Workflow failed: {e}", "error")
                return session

            finally:
                # Update state
                self.update_state("current_session", session)
                workflow_sessions = self.get_state("workflow_sessions", [])
                workflow_sessions.append(session)
                self.update_state("workflow_sessions", workflow_sessions)

        return (
            self.execute_with_tracking("run_complete_workflow", _workflow_operation)
            or {}
        )

    def _initialize_workflow_session(
        self,
        repo_url,
        user_prompt,
        workdir,
        enable_testing,
        create_venv,
        strict_testing,
        commit_changes,
        create_pr,
    ) -> Dict:
        """Initialize a new workflow session."""
        session = {
            "session_id": f"workflow_{int(time.time())}",
            "start_time": time.time(),
            "repo_url": repo_url,
            "user_prompt": user_prompt,
            "workdir": workdir,
            "enable_testing": enable_testing,
            "create_venv": create_venv,
            "strict_testing": strict_testing,
            "commit_changes": commit_changes,
            "create_pr": create_pr,
            "status": "running",
            "phases": {},
            "created_files": [],
            "test_results": None,
            "commit_info": None,
            "pr_info": None,
        }

        self.log(f"🚀 Starting AI agent workflow for: {repo_url}")
        self.log(f"📝 Task: {user_prompt}")
        self.log(f"🧪 Testing enabled: {enable_testing}")
        self.log(f"🐍 Virtual environment: {create_venv}")
        self.log(f"📝 Commit changes: {commit_changes}")
        self.log(f"🚀 Create PR: {create_pr}")

        return session

    def _generate_pr_metadata(self, user_prompt: str) -> tuple:
        """Generate branch topic and PR title using OpenAI."""

        if not self.openai_client:
            self.openai_client = OpenAI()

        system_prompt = (
            "You create concise git branch topics and pull request titles."
        )
        user_content = (
            "Provide a JSON object with keys 'topic' and 'title' based on the following "
            f"task: {user_prompt}. The topic must be a short, lowercase, hyphen-separated "
            "string suitable for a git branch. The title should be a concise description."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            data = json.loads(response.choices[0].message.content)
            topic = data.get("topic", "update")
            title = data.get("title", "Update")
        except Exception as e:
            self.log(f"Failed to generate PR metadata: {e}", "error")
            topic = re.sub(r"[^a-zA-Z0-9]+", "-", user_prompt.lower()).strip("-") or "update"
            title = user_prompt

        topic = re.sub(r"[^a-z0-9-]", "-", topic.lower()).strip("-")
        return topic, title

    def _setup_repository(
        self, repo_url: str, workdir: Optional[str], session: Dict, user_prompt: str
    ) -> Optional[str]:
        """Setup the repository for the workflow."""
        if workdir is None:
            workdir = "/Users/ishandutta/Documents/code"  # Use default from main.py

        # Generate branch topic and PR title
        topic, pr_title_raw = self._generate_pr_metadata(user_prompt)
        pr_title = f":robot: [orion] {pr_title_raw}"
        base_branch_name = f"orion/{topic}"
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(workdir, repo_name)

        # Clone repository
        clone_success = self.git_agent.clone_repository(repo_url, repo_path)
        if not clone_success:
            return None

        # Change to repo directory and validate
        original_dir = os.getcwd()
        os.chdir(repo_path)

        # Check if we're in a git repository
        status = self.git_agent.get_repository_status(repo_path)
        if not status:
            self.log("Error: Not a valid git repository", "error")
            os.chdir(original_dir)
            return None

        # Generate and create unique branch
        branch_name = self.git_agent.create_unique_branch(base_branch_name, repo_path)
        if not branch_name:
            os.chdir(original_dir)
            return None

        branch_created = self.git_agent.create_and_switch_branch(branch_name, repo_path)
        if not branch_created:
            os.chdir(original_dir)
            return None

        # Update session
        session["pr_title"] = pr_title
        session["branch_topic"] = topic
        session["phases"]["repository_setup"] = {
            "repo_path": repo_path,
            "branch_name": branch_name,
            "pr_title": pr_title,
            "status": "completed",
        }

        os.chdir(original_dir)
        return repo_path

    def _generate_code(self, user_prompt: str, repo_path: str, session: Dict) -> tuple:
        """Generate code using the AI agent."""
        # Generate code changes using AI
        self.log("Generating code changes using AI...")
        changes = self.ai_agent.generate_code_changes(user_prompt, repo_path)

        if not changes:
            return None, []

        # Apply the code changes
        created_files = self.ai_agent.make_code_changes(repo_path, changes)

        # Update session
        session["phases"]["code_generation"] = {
            "generated_code": changes,
            "created_files": created_files or [],
            "status": "completed",
        }
        session["created_files"] = created_files or []

        return changes, created_files or []

    def _setup_environment_and_test(
        self,
        repo_path: str,
        created_files: List[str],
        strict_testing: bool,
        session: Dict,
    ) -> bool:
        """Setup environment and run tests."""
        try:
            self.log("🧪 Setting up testing environment...")

            # Create virtual environment
            venv_path = self.env_agent.create_virtual_environment(repo_path)
            if not venv_path:
                return False

            venv_python = self.env_agent.get_venv_python(venv_path)

            # Install dependencies
            deps_installed = self.env_agent.install_dependencies(repo_path, venv_python)

            test_passed = True
            if deps_installed and created_files:
                # Test the generated code
                test_passed = self.test_agent.test_generated_code(
                    repo_path, venv_python, created_files
                )

                # Create/update requirements.txt
                self.env_agent.create_requirements_file(repo_path, venv_python)

                if not test_passed:
                    self.log("❌ Code tests failed!")
                    self.log(
                        "The generated code has errors that prevent it from running correctly."
                    )

                    if strict_testing:
                        self.log("❌ Strict testing enabled. Aborting workflow.")
                        return False
                    else:
                        self.log("⚠️ Continuing despite test failures...")
                        self.log("⚠️ The committed code may not work correctly!")
                else:
                    self.log("✅ All tests passed! Code is ready for commit.")
            else:
                self.log("⚠️ Dependency installation failed, skipping tests...")

            # Update session
            session["phases"]["environment_and_testing"] = {
                "venv_path": venv_path,
                "dependencies_installed": deps_installed,
                "tests_passed": test_passed,
                "test_results": self.test_agent.get_test_results(repo_path),
                "status": "completed",
            }
            session["test_results"] = self.test_agent.get_test_results(repo_path)

            return True

        except Exception as e:
            self.log(f"⚠️ Testing setup failed: {e}", "error")
            self.log("Continuing without testing...")
            return True

    def _commit_and_push(
        self,
        repo_path: str,
        user_prompt: str,
        create_pr: bool,
        repo_url: str,
        session: Dict,
    ) -> bool:
        """Commit changes and optionally create PR."""
        self.log("📝 Committing changes...")

        # Commit changes
        pr_title = session.get("pr_title", f":robot: [orion] {user_prompt}")
        commit_message = pr_title
        commit_success = self.git_agent.commit_changes(commit_message, repo_path)

        if not commit_success:
            return False

        pr_created = False
        if create_pr:
            # Get current branch
            current_branch = self.git_agent.get_state("current_branch")
            if current_branch:
                # Push branch
                push_success = self.git_agent.push_branch(current_branch, repo_path)

                if push_success:
                    # Create pull request
                    pr_body = (
                        f"This PR contains AI-generated changes for: {user_prompt}\n\n"
                        "Generated by Orion AI Agent"
                    )

                    pr_result = self.github_agent.create_pull_request(
                        repo_url, pr_title, pr_body, current_branch
                    )
                    pr_created = pr_result is not None
                else:
                    self.log("Failed to push branch. You may need to:", "error")
                    self.log("1. Fork the repository first")
                    self.log("2. Ensure you have push access")
                    self.log(
                        "3. Set up authentication (SSH keys or personal access token)"
                    )

        # Update session
        session["phases"]["git_operations"] = {
            "commit_success": commit_success,
            "commit_message": commit_message,
            "pr_title": pr_title,
            "pr_created": pr_created,
            "status": "completed",
        }

        if not create_pr:
            self.log(
                "💡 Changes committed locally. Use --create-pr to create a pull request."
            )

        return True

    def get_workflow_summary(self) -> Dict[str, any]:
        """
        Get a summary of all workflow sessions.

        Returns:
            Dict: Workflow summary
        """
        workflow_sessions = self.get_state("workflow_sessions", [])

        if not workflow_sessions:
            return {
                "total_sessions": 0,
                "successful_sessions": 0,
                "failed_sessions": 0,
                "success_rate": 0,
                "average_duration": 0,
            }

        total_sessions = len(workflow_sessions)
        successful_sessions = sum(
            1 for session in workflow_sessions if session.get("status") == "completed"
        )
        failed_sessions = total_sessions - successful_sessions

        total_duration = sum(
            session.get("duration", 0)
            for session in workflow_sessions
            if session.get("duration")
        )

        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "success_rate": (
                (successful_sessions / total_sessions * 100)
                if total_sessions > 0
                else 0
            ),
            "average_duration": (
                total_duration / total_sessions if total_sessions > 0 else 0
            ),
            "agents_summary": self._get_agents_summary(),
        }

    def _get_agents_summary(self) -> Dict[str, any]:
        """Get summary from all sub-agents."""
        return {
            "git_operations": self.git_agent.get_execution_summary(),
            "ai_generation": self.ai_agent.get_execution_summary(),
            "github_integration": self.github_agent.get_execution_summary(),
            "environment_manager": self.env_agent.get_execution_summary(),
            "code_tester": self.test_agent.get_execution_summary(),
        }

    def get_agent_status(self) -> Dict[str, any]:
        """
        Get the current status of all agents.

        Returns:
            Dict: Status of all agents
        """
        return {
            "orchestrator": {
                "name": self.name,
                "active_sessions": len(self.get_state("workflow_sessions", [])),
                "current_session": self.get_state("current_session") is not None,
            },
            "git_operations": {
                "name": self.git_agent.name,
                "current_repo": self.git_agent.get_state("current_repo"),
                "current_branch": self.git_agent.get_state("current_branch"),
            },
            "ai_generation": {
                "name": self.ai_agent.name,
                "model": self.ai_agent.get_state("model"),
                "files_created": len(self.ai_agent.get_state("created_files", [])),
            },
            "github_integration": {
                "name": self.github_agent.name,
                "authenticated": self.github_agent.get_state("authenticated"),
            },
            "environment_manager": {
                "name": self.env_agent.name,
                "active_environments": len(
                    self.env_agent.get_state("environments", {})
                ),
            },
            "code_tester": {
                "name": self.test_agent.name,
                "test_sessions": len(self.test_agent.get_state("test_history", [])),
            },
        }

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the Workflow Orchestrator Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "run": self.run_complete_workflow,
            "summary": self.get_workflow_summary,
            "status": self.get_agent_status,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
