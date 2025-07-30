"""
Environment Manager Agent for Orion AI Agent System

This agent handles virtual environment management and dependency installation.
"""

import os
import platform
import subprocess
import sys
import time
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class EnvironmentManagerAgent(BaseAgent):
    """
    Agent responsible for environment management operations.

    Capabilities:
    - Create virtual environments
    - Install dependencies
    - Manage Python environments
    - Generate requirements files
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Environment Manager Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("EnvironmentManager", debug)
        self.update_state("environments", {})
        self.update_state("current_environment", None)
        self.update_state("installed_packages", {})

    def create_virtual_environment(
        self, repo_path: str, env_name: str = ".venv"
    ) -> Optional[str]:
        """
        Create a virtual environment for the repository.

        Args:
            repo_path: Path to the repository
            env_name: Name of the virtual environment directory

        Returns:
            str: Path to the virtual environment, or None if failed
        """

        def _create_venv_operation():
            venv_path = os.path.join(repo_path, env_name)

            if os.path.exists(venv_path):
                self.log("🔄 Virtual environment already exists, using existing one")
                self.update_state("current_environment", venv_path)
                return venv_path

            self.log("🐍 Creating virtual environment...")
            subprocess.run(
                ["python", "-m", "venv", venv_path], check=True, cwd=repo_path
            )
            self.log("✅ Virtual environment created successfully")

            # Update state
            self.update_state("current_environment", venv_path)
            environments = self.get_state("environments", {})
            environments[repo_path] = {
                "path": venv_path,
                "created_at": time.time(),
                "python_version": platform.python_version(),
                "packages": [],
            }
            self.update_state("environments", environments)

            return venv_path

        return self.execute_with_tracking(
            "create_virtual_environment", _create_venv_operation
        )

    def get_venv_python(self, venv_path: str) -> str:
        """
        Get the path to the Python executable in the virtual environment.

        Args:
            venv_path: Path to the virtual environment

        Returns:
            str: Path to the Python executable
        """
        if platform.system() == "Windows":
            return os.path.join(venv_path, "Scripts", "python.exe")
        else:
            return os.path.join(venv_path, "bin", "python")

    def install_dependencies(
        self, repo_path: str, venv_python: Optional[str] = None
    ) -> bool:
        """
        Install dependencies from requirements.txt or detect and install common ones.

        Args:
            repo_path: Path to the repository
            venv_python: Path to the virtual environment Python executable

        Returns:
            bool: True if installation was successful
        """

        def _install_deps_operation():
            if not venv_python:
                current_env = self.get_state("current_environment")
                if not current_env:
                    raise ValueError(
                        "No virtual environment specified and no current environment set"
                    )
                python_exec = self.get_venv_python(current_env)
            else:
                python_exec = venv_python

            # First, upgrade pip
            self.log("📦 Upgrading pip...")
            subprocess.run(
                [python_exec, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                cwd=repo_path,
                capture_output=True,
            )

            # Check for requirements.txt
            requirements_file = os.path.join(repo_path, "requirements.txt")
            installed_packages = []

            if os.path.exists(requirements_file):
                self.log("📋 Installing dependencies from requirements.txt...")
                subprocess.run(
                    [python_exec, "-m", "pip", "install", "-r", "requirements.txt"],
                    check=True,
                    cwd=repo_path,
                )
                self.log("✅ Dependencies installed from requirements.txt")

                # Read requirements to track installed packages
                with open(requirements_file, "r") as f:
                    installed_packages = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
            else:
                # If no requirements.txt, install common dependencies for AI/ML projects
                self.log(
                    "📦 No requirements.txt found, installing common dependencies..."
                )
                common_deps = ["torch", "transformers", "pillow", "numpy", "requests"]

                for dep in common_deps:
                    try:
                        self.log(f"  Installing {dep}...")
                        subprocess.run(
                            [python_exec, "-m", "pip", "install", dep],
                            check=True,
                            cwd=repo_path,
                            capture_output=True,
                        )
                        installed_packages.append(dep)
                    except subprocess.CalledProcessError:
                        self.log(f"  ⚠️ Failed to install {dep}, skipping...", "warning")

                self.log("✅ Common dependencies installed")

            # Update state
            environments = self.get_state("environments", {})
            if repo_path in environments:
                environments[repo_path]["packages"] = installed_packages
                environments[repo_path]["last_install"] = time.time()
                self.update_state("environments", environments)

            installed_packages_state = self.get_state("installed_packages", {})
            installed_packages_state[repo_path] = installed_packages
            self.update_state("installed_packages", installed_packages_state)

            return True

        return (
            self.execute_with_tracking("install_dependencies", _install_deps_operation)
            is not None
        )

    def create_requirements_file(
        self, repo_path: str, venv_python: Optional[str] = None
    ) -> bool:
        """
        Create or update requirements.txt with installed packages.

        Args:
            repo_path: Path to the repository
            venv_python: Path to the virtual environment Python executable

        Returns:
            bool: True if successful, False otherwise
        """

        def _create_requirements_operation():
            if not venv_python:
                current_env = self.get_state("current_environment")
                if not current_env:
                    raise ValueError(
                        "No virtual environment specified and no current environment set"
                    )
                python_exec = self.get_venv_python(current_env)
            else:
                python_exec = venv_python

            self.log("📝 Generating requirements.txt...")
            result = subprocess.run(
                [python_exec, "-m", "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True,
                cwd=repo_path,
            )

            requirements_path = os.path.join(repo_path, "requirements.txt")
            with open(requirements_path, "w") as f:
                f.write(result.stdout)

            self.log("✅ requirements.txt created/updated")

            # Update state
            package_count = (
                len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            )
            environments = self.get_state("environments", {})
            if repo_path in environments:
                environments[repo_path]["requirements_generated"] = time.time()
                environments[repo_path]["package_count"] = package_count
                self.update_state("environments", environments)

            return True

        return (
            self.execute_with_tracking(
                "create_requirements_file", _create_requirements_operation
            )
            is not None
        )

    def get_environment_info(self, repo_path: str) -> Optional[Dict]:
        """
        Get information about the environment for a specific repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict: Environment information, or None if not found
        """
        environments = self.get_state("environments", {})
        if repo_path in environments:
            env_info = environments[repo_path].copy()

            # Add current status
            venv_path = env_info.get("path")
            if venv_path and os.path.exists(venv_path):
                env_info["status"] = "active"
                env_info["python_executable"] = self.get_venv_python(venv_path)
            else:
                env_info["status"] = "missing"

            return env_info

        return None

    def list_installed_packages(
        self, repo_path: str, venv_python: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        List all installed packages in the virtual environment.

        Args:
            repo_path: Path to the repository
            venv_python: Path to the virtual environment Python executable

        Returns:
            List[str]: List of installed packages, or None if failed
        """

        def _list_packages_operation():
            if not venv_python:
                current_env = self.get_state("current_environment")
                if not current_env:
                    raise ValueError(
                        "No virtual environment specified and no current environment set"
                    )
                python_exec = self.get_venv_python(current_env)
            else:
                python_exec = venv_python

            result = subprocess.run(
                [python_exec, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
                cwd=repo_path,
            )

            packages = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    packages.append(line.strip())

            return packages

        return self.execute_with_tracking(
            "list_installed_packages", _list_packages_operation
        )

    def cleanup_environment(self, repo_path: str) -> bool:
        """
        Clean up the virtual environment for a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            bool: True if successful, False otherwise
        """

        def _cleanup_operation():
            environments = self.get_state("environments", {})
            if repo_path not in environments:
                self.log(f"No environment found for {repo_path}", "warning")
                return False

            env_info = environments[repo_path]
            venv_path = env_info.get("path")

            if venv_path and os.path.exists(venv_path):
                import shutil

                shutil.rmtree(venv_path)
                self.log(f"🗑️ Removed virtual environment: {venv_path}")

            # Remove from state
            del environments[repo_path]
            self.update_state("environments", environments)

            installed_packages = self.get_state("installed_packages", {})
            if repo_path in installed_packages:
                del installed_packages[repo_path]
                self.update_state("installed_packages", installed_packages)

            return True

        return (
            self.execute_with_tracking("cleanup_environment", _cleanup_operation)
            is not None
        )

    def get_environment_summary(self) -> Dict[str, any]:
        """
        Get a summary of all managed environments.

        Returns:
            Dict: Summary of environments
        """
        environments = self.get_state("environments", {})

        summary = {
            "total_environments": len(environments),
            "active_environments": 0,
            "total_packages": 0,
            "environments": [],
        }

        for repo_path, env_info in environments.items():
            venv_path = env_info.get("path")
            is_active = venv_path and os.path.exists(venv_path)

            if is_active:
                summary["active_environments"] += 1

            package_count = env_info.get("package_count", 0)
            summary["total_packages"] += package_count

            env_summary = {
                "repo_path": repo_path,
                "status": "active" if is_active else "missing",
                "created_at": env_info.get("created_at"),
                "package_count": package_count,
                "python_version": env_info.get("python_version"),
            }
            summary["environments"].append(env_summary)

        return summary

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the Environment Manager Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "create_venv": self.create_virtual_environment,
            "install_deps": self.install_dependencies,
            "create_requirements": self.create_requirements_file,
            "get_info": self.get_environment_info,
            "list_packages": self.list_installed_packages,
            "cleanup": self.cleanup_environment,
            "summary": self.get_environment_summary,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
