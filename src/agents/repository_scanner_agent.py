"""
Repository Scanner Agent for Orion AI Agent System

This agent handles repository scanning, file discovery, and basic code analysis
to understand the structure and content of existing codebases.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class RepositoryScannerAgent(BaseAgent):
    """
    Agent responsible for scanning and analyzing repository structure and content.

    Capabilities:
    - Scan repository file structure
    - Analyze file types and sizes
    - Extract basic code information (functions, classes, imports)
    - Build repository inventory
    - Identify modification targets
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Repository Scanner Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("RepositoryScanner", debug)
        self.update_state("scanned_repositories", {})
        self.update_state("file_inventory", {})
        self.update_state("code_analysis", {})

    def scan_repository(self, repo_path: str) -> Dict:
        """
        Perform a comprehensive scan of the repository.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Dict: Comprehensive repository analysis
        """

        def _scan_operation():
            self.log(f"🔍 Scanning repository: {repo_path}")

            if not os.path.exists(repo_path):
                raise Exception(f"Repository path does not exist: {repo_path}")

            # Build file inventory
            file_inventory = self._build_file_inventory(repo_path)

            # Analyze code files
            code_analysis = self._analyze_code_files(repo_path, file_inventory)

            # Create repository summary
            repo_summary = {
                "repo_path": repo_path,
                "total_files": len(file_inventory),
                "file_inventory": file_inventory,
                "code_analysis": code_analysis,
                "file_types": self._categorize_files(file_inventory),
                "python_files": [f for f in file_inventory.keys() if f.endswith(".py")],
                "modification_candidates": self._identify_modification_candidates(
                    file_inventory, code_analysis
                ),
            }

            # Update state
            scanned_repos = self.get_state("scanned_repositories", {})
            scanned_repos[repo_path] = repo_summary
            self.update_state("scanned_repositories", scanned_repos)
            self.update_state("file_inventory", file_inventory)
            self.update_state("code_analysis", code_analysis)

            self.log(f"✅ Repository scan complete. Found {len(file_inventory)} files")
            return repo_summary

        return self.execute_with_tracking("scan_repository", _scan_operation)

    def _build_file_inventory(self, repo_path: str) -> Dict[str, Dict]:
        """
        Build an inventory of all files in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict: File inventory with metadata
        """
        file_inventory = {}
        repo_pathobj = Path(repo_path)

        # Define files/directories to ignore
        ignore_patterns = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            "dist",
            "build",
            ".DS_Store",
        }

        for file_path in repo_pathobj.rglob("*"):
            if file_path.is_file():
                # Skip ignored files/directories
                if any(ignore in file_path.parts for ignore in ignore_patterns):
                    continue

                relative_path = str(file_path.relative_to(repo_pathobj))

                try:
                    file_stats = file_path.stat()
                    file_inventory[relative_path] = {
                        "absolute_path": str(file_path),
                        "size_bytes": file_stats.st_size,
                        "extension": file_path.suffix,
                        "is_python": file_path.suffix == ".py",
                        "is_text": self._is_text_file(file_path),
                        "last_modified": file_stats.st_mtime,
                    }
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue

        return file_inventory

    def _is_text_file(self, file_path: Path) -> bool:
        """
        Check if a file is likely a text file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if file appears to be text
        """
        text_extensions = {
            ".py",
            ".txt",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".cfg",
            ".ini",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".xml",
            ".csv",
            ".sql",
            ".dockerfile",
            ".gitignore",
            ".gitattributes",
        }

        if file_path.suffix.lower() in text_extensions:
            return True

        # Check if file has no extension but might be text (like Dockerfile)
        if not file_path.suffix:
            try:
                with open(file_path, "rb") as f:
                    chunk = f.read(1024)
                    return chunk.isascii() or not chunk
            except:
                return False

        return False

    def _analyze_code_files(self, repo_path: str, file_inventory: Dict) -> Dict:
        """
        Analyze Python code files to extract structure information.

        Args:
            repo_path: Path to the repository
            file_inventory: File inventory from scanning

        Returns:
            Dict: Code analysis results
        """
        code_analysis = {}

        for relative_path, file_info in file_inventory.items():
            if file_info["is_python"]:
                try:
                    analysis = self._analyze_python_file(file_info["absolute_path"])
                    if analysis:
                        code_analysis[relative_path] = analysis
                except Exception as e:
                    self.log(f"⚠️ Could not analyze {relative_path}: {e}", "warning")

        return code_analysis

    def _analyze_python_file(self, file_path: str) -> Optional[Dict]:
        """
        Analyze a single Python file to extract structure information.

        Args:
            file_path: Path to the Python file

        Returns:
            Optional[Dict]: Analysis results or None if failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "imports": self._extract_imports(content),
                "classes": self._extract_classes(content),
                "functions": self._extract_functions(content),
                "constants": self._extract_constants(content),
                "docstring": self._extract_module_docstring(content),
                "line_count": len(content.split("\n")),
                "has_main_guard": 'if __name__ == "__main__"' in content,
            }

            return analysis

        except (UnicodeDecodeError, OSError):
            return None

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code."""
        imports = []

        # Match import statements
        import_patterns = [
            r"^import\s+([^\n]+)",
            r"^from\s+([^\s]+)\s+import\s+([^\n]+)",
        ]

        for line in content.split("\n"):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    imports.append(line)
                    break

        return imports

    def _extract_classes(self, content: str) -> List[Dict]:
        """Extract class definitions from Python code."""
        classes = []

        class_pattern = r"^class\s+(\w+)(?:\([^)]*\))?:"

        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            match = re.match(class_pattern, line)
            if match:
                class_name = match.group(1)
                classes.append(
                    {"name": class_name, "line_number": i, "definition": line}
                )

        return classes

    def _extract_functions(self, content: str) -> List[Dict]:
        """Extract function definitions from Python code."""
        functions = []

        function_pattern = r"^def\s+(\w+)\s*\([^)]*\):"

        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            match = re.match(function_pattern, line)
            if match:
                func_name = match.group(1)
                functions.append(
                    {"name": func_name, "line_number": i, "definition": line}
                )

        return functions

    def _extract_constants(self, content: str) -> List[str]:
        """Extract constants (ALL_CAPS variables) from Python code."""
        constants = []

        constant_pattern = r"^([A-Z_][A-Z0-9_]*)\s*="

        for line in content.split("\n"):
            line = line.strip()
            match = re.match(constant_pattern, line)
            if match:
                constants.append(match.group(1))

        return constants

    def _extract_module_docstring(self, content: str) -> Optional[str]:
        """Extract module-level docstring."""
        # Look for triple-quoted strings at the beginning of the file
        docstring_pattern = r'^\s*"""(.*?)"""'
        match = re.search(docstring_pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Try single quotes
        docstring_pattern = r"^\s*'''(.*?)'''"
        match = re.search(docstring_pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return None

    def _categorize_files(self, file_inventory: Dict) -> Dict[str, int]:
        """
        Categorize files by type.

        Args:
            file_inventory: File inventory

        Returns:
            Dict: File type counts
        """
        categories = {}

        for file_info in file_inventory.values():
            ext = file_info["extension"].lower()
            if not ext:
                ext = "no_extension"

            categories[ext] = categories.get(ext, 0) + 1

        return categories

    def _identify_modification_candidates(
        self, file_inventory: Dict, code_analysis: Dict
    ) -> List[str]:
        """
        Identify files that are good candidates for modification.

        Args:
            file_inventory: File inventory
            code_analysis: Code analysis results

        Returns:
            List[str]: List of files suitable for modification
        """
        candidates = []

        for relative_path, file_info in file_inventory.items():
            # Python files are primary candidates
            if file_info["is_python"]:
                # Skip very large files (>10KB) or very small files (<50 bytes)
                if 50 <= file_info["size_bytes"] <= 10000:
                    candidates.append(relative_path)

            # Configuration files
            elif file_info["extension"] in [".json", ".yaml", ".yml", ".toml", ".cfg"]:
                candidates.append(relative_path)

        return candidates

    def get_file_content(
        self, repo_path: str, relative_file_path: str
    ) -> Optional[str]:
        """
        Get the content of a specific file.

        Args:
            repo_path: Path to the repository
            relative_file_path: Relative path to the file within the repository

        Returns:
            Optional[str]: File content or None if failed
        """

        def _read_operation():
            file_path = os.path.join(repo_path, relative_file_path)

            if not os.path.exists(file_path):
                raise Exception(f"File does not exist: {file_path}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                self.log(f"📖 Read file: {relative_file_path}")
                return content

            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

                self.log(f"📖 Read file (latin-1): {relative_file_path}")
                return content

        return self.execute_with_tracking("get_file_content", _read_operation)

    def find_files_by_pattern(self, repo_path: str, pattern: str) -> List[str]:
        """
        Find files matching a specific pattern.

        Args:
            repo_path: Path to the repository
            pattern: Pattern to match (can be filename, extension, or regex)

        Returns:
            List[str]: List of matching file paths
        """
        scanned_repos = self.get_state("scanned_repositories", {})

        if repo_path not in scanned_repos:
            self.log(f"Repository not scanned: {repo_path}. Scanning now...")
            self.scan_repository(repo_path)
            scanned_repos = self.get_state("scanned_repositories", {})

        file_inventory = scanned_repos[repo_path]["file_inventory"]
        matching_files = []

        for relative_path in file_inventory.keys():
            # Simple pattern matching
            if (
                pattern.lower() in relative_path.lower()
                or relative_path.endswith(pattern)
                or re.search(pattern, relative_path, re.IGNORECASE)
            ):
                matching_files.append(relative_path)

        return matching_files

    def get_repository_summary(self, repo_path: str) -> Optional[Dict]:
        """
        Get a summary of a scanned repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Optional[Dict]: Repository summary or None if not scanned
        """
        scanned_repos = self.get_state("scanned_repositories", {})
        return scanned_repos.get(repo_path)

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the Repository Scanner Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "scan": self.scan_repository,
            "read": self.get_file_content,
            "find": self.find_files_by_pattern,
            "summary": self.get_repository_summary,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
