"""
Task Classifier Agent for Orion AI Agent System

This agent handles task analysis and classification to determine the appropriate
action (modify existing files vs create new files) and identify target files.
"""

import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class TaskClassifierAgent(BaseAgent):
    """
    Agent responsible for analyzing and classifying user tasks.

    Capabilities:
    - Classify tasks as modification vs creation
    - Extract file names mentioned in prompts
    - Identify task types (bug fix, feature, refactor, etc.)
    - Determine task scope and complexity
    - Suggest target files for modification
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Task Classifier Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("TaskClassifier", debug)
        self.update_state("classified_tasks", [])
        self.update_state("task_patterns", self._initialize_task_patterns())

    def _initialize_task_patterns(self) -> Dict:
        """
        Initialize patterns for task classification.

        Returns:
            Dict: Classification patterns and keywords
        """
        return {
            "modification_keywords": {
                "modify",
                "update",
                "change",
                "fix",
                "edit",
                "alter",
                "revise",
                "improve",
                "enhance",
                "refactor",
                "optimize",
                "debug",
                "patch",
                "correct",
                "adjust",
                "tweak",
                "replace",
                "remove",
                "delete",
            },
            "creation_keywords": {
                "create",
                "add",
                "new",
                "build",
                "make",
                "generate",
                "implement",
                "develop",
                "write",
                "design",
                "construct",
                "establish",
                "setup",
                "initialize",
                "start",
                "begin",
            },
            "file_patterns": [
                # Full file paths with directories
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.py)",  # Python files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.js)",  # JavaScript files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.json)",  # JSON files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.yaml)",  # YAML files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.yml)",  # YML files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.toml)",  # TOML files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.cfg)",  # Config files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.ini)",  # INI files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.md)",  # Markdown files with paths
                r"([a-zA-Z_][a-zA-Z0-9_/.-]*\.txt)",  # Text files with paths
                # Simple filenames (fallback)
                r"([a-zA-Z_][a-zA-Z0-9_]*\.py)",  # Python files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.js)",  # JavaScript files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.json)",  # JSON files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.yaml)",  # YAML files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.yml)",  # YML files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.toml)",  # TOML files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.cfg)",  # Config files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.ini)",  # INI files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.md)",  # Markdown files
                r"([a-zA-Z_][a-zA-Z0-9_]*\.txt)",  # Text files
            ],
            "task_types": {
                "bug_fix": {
                    "fix",
                    "bug",
                    "error",
                    "issue",
                    "problem",
                    "broken",
                    "crash",
                },
                "feature": {"feature", "functionality", "capability", "add", "new"},
                "refactor": {
                    "refactor",
                    "restructure",
                    "reorganize",
                    "clean",
                    "optimize",
                },
                "enhancement": {"improve", "enhance", "better", "upgrade", "extend"},
                "maintenance": {"update", "maintain", "sync", "merge", "integrate"},
                "documentation": {"document", "comment", "docstring", "readme", "docs"},
            },
        }

    def classify_task(
        self, user_prompt: str, repository_context: Optional[Dict] = None
    ) -> Dict:
        """
        Classify a user task based on the prompt and repository context.

        Args:
            user_prompt: The user's task description
            repository_context: Optional context about the repository

        Returns:
            Dict: Task classification results
        """

        def _classify_operation():
            self.log(f"🔍 Classifying task: {user_prompt[:100]}...")

            # Clean and normalize the prompt
            prompt_lower = user_prompt.lower().strip()

            # Extract mentioned files
            mentioned_files = self._extract_mentioned_files(user_prompt)

            # Determine primary action
            primary_action = self._determine_primary_action(prompt_lower)

            # Classify task type
            task_type = self._classify_task_type(prompt_lower)

            # Determine scope
            task_scope = self._determine_task_scope(prompt_lower, mentioned_files)

            # Assess complexity
            complexity = self._assess_complexity(
                prompt_lower, mentioned_files, repository_context
            )

            # Generate suggestions
            suggestions = self._generate_suggestions(
                prompt_lower, mentioned_files, primary_action, repository_context
            )

            # Determine if repository scan is needed
            has_specific_files = len(mentioned_files) > 0
            requires_scan = (
                primary_action == "modify" and not has_specific_files
            ) or has_specific_files

            classification = {
                "original_prompt": user_prompt,
                "primary_action": primary_action,
                "task_type": task_type,
                "scope": task_scope,
                "complexity": complexity,
                "mentioned_files": mentioned_files,
                "target_files": suggestions.get("target_files", []),
                "suggested_approach": suggestions.get("approach", ""),
                "confidence": self._calculate_confidence(prompt_lower, mentioned_files),
                "requires_repository_scan": requires_scan,
            }

            # Update state
            classified_tasks = self.get_state("classified_tasks", [])
            classified_tasks.append(classification)
            self.update_state("classified_tasks", classified_tasks)

            self.log(f"✅ Task classified as: {primary_action} ({task_type})")
            return classification

        return self.execute_with_tracking("classify_task", _classify_operation)

    def _extract_mentioned_files(self, prompt: str) -> List[str]:
        """
        Extract file names mentioned in the prompt.

        Args:
            prompt: User prompt

        Returns:
            List[str]: List of mentioned file names
        """
        mentioned_files = []
        patterns = self.get_state("task_patterns", {}).get("file_patterns", [])

        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            mentioned_files.extend(matches)

        # Also look for files mentioned without extensions
        # Pattern for "in file_name" or "file_name.py"
        file_mention_patterns = [
            r"(?:in|file|script)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:file|script|module)",
        ]

        for pattern in file_mention_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            for match in matches:
                if (
                    match not in mentioned_files and len(match) > 2
                ):  # Skip very short matches
                    mentioned_files.append(match)

        return list(set(mentioned_files))  # Remove duplicates

    def _determine_primary_action(self, prompt_lower: str) -> str:
        """
        Determine the primary action (modify, create, or analyze).

        Args:
            prompt_lower: Lowercase prompt

        Returns:
            str: Primary action
        """
        patterns = self.get_state("task_patterns", {})
        modification_keywords = patterns.get("modification_keywords", set())
        creation_keywords = patterns.get("creation_keywords", set())

        modification_score = sum(
            1 for keyword in modification_keywords if keyword in prompt_lower
        )
        creation_score = sum(
            1 for keyword in creation_keywords if keyword in prompt_lower
        )

        # Special cases
        if "explain" in prompt_lower or "analyze" in prompt_lower:
            return "analyze"

        if modification_score > creation_score:
            return "modify"
        elif creation_score > modification_score:
            return "create"
        else:
            # If scores are equal, look for context clues
            if any(word in prompt_lower for word in ["existing", "current", "in the"]):
                return "modify"
            else:
                return "create"

    def _classify_task_type(self, prompt_lower: str) -> str:
        """
        Classify the type of task.

        Args:
            prompt_lower: Lowercase prompt

        Returns:
            str: Task type
        """
        task_types = self.get_state("task_patterns", {}).get("task_types", {})

        scores = {}
        for task_type, keywords in task_types.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower)
            if score > 0:
                scores[task_type] = score

        if scores:
            return max(scores, key=scores.get)
        else:
            return "general"

    def _determine_task_scope(
        self, prompt_lower: str, mentioned_files: List[str]
    ) -> str:
        """
        Determine the scope of the task.

        Args:
            prompt_lower: Lowercase prompt
            mentioned_files: List of mentioned files

        Returns:
            str: Task scope
        """
        # Keywords that indicate scope
        single_file_indicators = ["function", "method", "class", "variable", "line"]
        multi_file_indicators = [
            "module",
            "package",
            "system",
            "application",
            "project",
        ]

        single_file_score = sum(
            1 for indicator in single_file_indicators if indicator in prompt_lower
        )
        multi_file_score = sum(
            1 for indicator in multi_file_indicators if indicator in prompt_lower
        )

        if len(mentioned_files) > 1:
            return "multi_file"
        elif len(mentioned_files) == 1:
            return "single_file"
        elif multi_file_score > single_file_score:
            return "multi_file"
        else:
            return "single_file"

    def _assess_complexity(
        self,
        prompt_lower: str,
        mentioned_files: List[str],
        repository_context: Optional[Dict],
    ) -> str:
        """
        Assess the complexity of the task.

        Args:
            prompt_lower: Lowercase prompt
            mentioned_files: List of mentioned files
            repository_context: Repository context

        Returns:
            str: Complexity level
        """
        complexity_score = 0

        # Factors that increase complexity
        high_complexity_indicators = [
            "complex",
            "multiple",
            "integrate",
            "refactor",
            "architecture",
            "system",
            "database",
            "api",
            "authentication",
            "security",
        ]

        medium_complexity_indicators = [
            "add",
            "implement",
            "create",
            "modify",
            "update",
            "enhance",
        ]

        low_complexity_indicators = [
            "fix",
            "change",
            "replace",
            "remove",
            "simple",
            "basic",
        ]

        for indicator in high_complexity_indicators:
            if indicator in prompt_lower:
                complexity_score += 3

        for indicator in medium_complexity_indicators:
            if indicator in prompt_lower:
                complexity_score += 2

        for indicator in low_complexity_indicators:
            if indicator in prompt_lower:
                complexity_score += 1

        # File count affects complexity
        if len(mentioned_files) > 3:
            complexity_score += 3
        elif len(mentioned_files) > 1:
            complexity_score += 1

        # Repository size affects complexity
        if repository_context:
            total_files = repository_context.get("total_files", 0)
            if total_files > 50:
                complexity_score += 1

        if complexity_score >= 6:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"

    def _generate_suggestions(
        self,
        prompt_lower: str,
        mentioned_files: List[str],
        primary_action: str,
        repository_context: Optional[Dict],
    ) -> Dict:
        """
        Generate suggestions for task execution.

        Args:
            prompt_lower: Lowercase prompt
            mentioned_files: List of mentioned files
            primary_action: Primary action determined
            repository_context: Repository context

        Returns:
            Dict: Suggestions for task execution
        """
        suggestions = {"target_files": mentioned_files.copy(), "approach": ""}

        if primary_action == "modify":
            if mentioned_files:
                suggestions["approach"] = (
                    f"Modify the specified files: {', '.join(mentioned_files)}"
                )
            else:
                suggestions["approach"] = (
                    "Scan repository to identify files that need modification"
                )

                # Try to suggest files based on keywords
                if repository_context:
                    python_files = repository_context.get("python_files", [])

                    # Look for files that might be relevant based on prompt keywords
                    relevant_files = []
                    for file_path in python_files:
                        file_name_lower = file_path.lower()
                        if any(
                            keyword in file_name_lower
                            for keyword in prompt_lower.split()
                        ):
                            relevant_files.append(file_path)

                    if relevant_files:
                        suggestions["target_files"] = relevant_files[
                            :3
                        ]  # Limit to top 3
                        suggestions[
                            "approach"
                        ] += f". Suggested files: {', '.join(relevant_files[:3])}"

        elif primary_action == "create":
            suggestions["approach"] = "Create new files as specified"

            # If no files mentioned, suggest based on task type
            if not mentioned_files:
                if "script" in prompt_lower:
                    suggestions["target_files"] = ["new_script.py"]
                elif "module" in prompt_lower:
                    suggestions["target_files"] = ["new_module.py"]
                elif "class" in prompt_lower:
                    suggestions["target_files"] = ["new_class.py"]
                else:
                    suggestions["target_files"] = ["generated_code.py"]

        else:  # analyze
            suggestions["approach"] = "Analyze the repository or specified files"

        return suggestions

    def _calculate_confidence(
        self, prompt_lower: str, mentioned_files: List[str]
    ) -> float:
        """
        Calculate confidence in the classification.

        Args:
            prompt_lower: Lowercase prompt
            mentioned_files: List of mentioned files

        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Explicit file mentions increase confidence
        if mentioned_files:
            confidence += 0.3

        # Clear action words increase confidence
        patterns = self.get_state("task_patterns", {})
        all_keywords = patterns.get("modification_keywords", set()) | patterns.get(
            "creation_keywords", set()
        )

        keyword_matches = sum(1 for keyword in all_keywords if keyword in prompt_lower)
        confidence += min(keyword_matches * 0.1, 0.3)

        # Specific task type indicators increase confidence
        task_types = patterns.get("task_types", {})
        for keywords in task_types.values():
            if any(keyword in prompt_lower for keyword in keywords):
                confidence += 0.1
                break

        return min(confidence, 1.0)

    def validate_and_find_files(
        self, mentioned_files: List[str], repository_context: Optional[Dict] = None
    ) -> List[str]:
        """
        Validate mentioned files and find their actual paths in the repository.

        Args:
            mentioned_files: List of files mentioned in the prompt
            repository_context: Repository context with file inventory

        Returns:
            List[str]: List of validated file paths that actually exist
        """

        def _validate_operation():
            validated_files = []

            if not repository_context or not mentioned_files:
                return mentioned_files  # Return as-is if no context

            file_inventory = repository_context.get("file_inventory", {})

            for mentioned_file in mentioned_files:
                # Direct match
                if mentioned_file in file_inventory:
                    validated_files.append(mentioned_file)
                    continue

                # Look for files that end with the mentioned filename
                found = False
                for repo_file in file_inventory.keys():
                    if (
                        repo_file.endswith(mentioned_file)
                        or mentioned_file in repo_file
                    ):
                        validated_files.append(repo_file)
                        found = True
                        break

                # If not found in repository, keep the original (might be a new file)
                if not found:
                    validated_files.append(mentioned_file)

            self.log(f"💡 Validated {len(validated_files)} files from mentions")
            return validated_files

        return self.execute_with_tracking(
            "validate_and_find_files", _validate_operation
        )

    def suggest_target_files(
        self, task_classification: Dict, repository_context: Optional[Dict] = None
    ) -> List[str]:
        """
        Suggest target files based on task classification and repository context.

        Args:
            task_classification: Result from classify_task
            repository_context: Repository context

        Returns:
            List[str]: Suggested target files
        """

        def _suggest_operation():
            primary_action = task_classification.get("primary_action", "")
            mentioned_files = task_classification.get("mentioned_files", [])
            task_type = task_classification.get("task_type", "")

            suggestions = []

            if mentioned_files:
                # Start with explicitly mentioned files
                suggestions.extend(mentioned_files)

            if repository_context and primary_action == "modify":
                # Look for relevant files in the repository
                python_files = repository_context.get("python_files", [])
                modification_candidates = repository_context.get(
                    "modification_candidates", []
                )

                # Filter based on task type
                if task_type == "bug_fix":
                    # Look for test files or main modules
                    suggestions.extend(
                        [
                            f
                            for f in python_files
                            if "test" in f.lower() or "main" in f.lower()
                        ]
                    )

                elif task_type == "feature":
                    # Look for main application files
                    suggestions.extend(
                        [
                            f
                            for f in modification_candidates
                            if "main" in f.lower() or "app" in f.lower()
                        ]
                    )

                elif task_type == "documentation":
                    # Look for files that might need documentation
                    suggestions.extend(
                        [f for f in python_files if not f.lower().startswith("test")]
                    )

            # Remove duplicates and limit results
            unique_suggestions = list(dict.fromkeys(suggestions))[:5]

            self.log(f"💡 Suggested {len(unique_suggestions)} target files")
            return unique_suggestions

        return self.execute_with_tracking("suggest_target_files", _suggest_operation)

    def get_classification_history(self) -> List[Dict]:
        """
        Get the history of task classifications.

        Returns:
            List[Dict]: List of classification records
        """
        return self.get_state("classified_tasks", [])

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the Task Classifier Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "classify": self.classify_task,
            "suggest": self.suggest_target_files,
            "history": self.get_classification_history,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
