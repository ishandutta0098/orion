"""
AI Generator Agent for Orion AI Agent System

This agent handles AI-powered code generation using LangChain and OpenAI.
"""

import os
import re
import sys
import time
from typing import Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class AIGeneratorAgent(BaseAgent):
    """
    Agent responsible for AI-powered code generation.

    Capabilities:
    - Generate code based on prompts
    - Extract and process AI responses
    - Manage code generation state and history
    """

    def __init__(
        self, model: str = "gpt-4o-mini", temperature: float = 0.1, debug: bool = False
    ):
        """
        Initialize the AI Generator Agent.

        Args:
            model: OpenAI model to use
            temperature: Temperature for generation
            debug: Whether to enable debug mode
        """
        super().__init__("AIGenerator", debug)
        self.model = model
        self.temperature = temperature

        # Initialize LangChain components
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.update_state("model", model)
        self.update_state("temperature", temperature)
        self.update_state("generated_code", [])
        self.update_state("created_files", [])

    def generate_code_changes(
        self, prompt: str, repo_path: str, context: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate code changes for the repository based on the prompt.

        Args:
            prompt: Task description for the AI
            repo_path: Path to the repository
            context: Additional context for generation

        Returns:
            str: Generated code changes, or None if failed
        """

        def _generation_operation():
            # Create enhanced prompt template
            template = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a helpful AI engineer. Analyze the repository and provide specific code implementations. "
                        "For each file you want to create or modify, provide the content in the following format:\n"
                        "FILE: filename.py\n"
                        "```python\n"
                        "# Complete file content here\n"
                        "```\n"
                        "Be sure to include all necessary imports and complete, runnable code.",
                    ),
                    (
                        "user",
                        "Repository path: {repo_path}\nTask: {prompt}\n\n"
                        "Additional context: {context}\n\n"
                        "Please provide the complete code files needed to accomplish this task. "
                        "Include proper imports, error handling, and documentation.",
                    ),
                ]
            )

            # Use the modern LangChain approach
            chain = template | self.llm | StrOutputParser()

            # Prepare context
            context_str = ""
            if context:
                context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])

            self.log(f"Generating code for prompt: {prompt}")
            result = chain.invoke(
                {
                    "prompt": prompt,
                    "repo_path": repo_path,
                    "context": context_str or "No additional context provided",
                }
            )

            # Update state
            generation_info = {
                "prompt": prompt,
                "repo_path": repo_path,
                "context": context,
                "result": result,
                "timestamp": time.time(),
                "model": self.model,
                "temperature": self.temperature,
            }

            generated_code = self.get_state("generated_code", [])
            generated_code.append(generation_info)
            self.update_state("generated_code", generated_code)

            return result

        return self.execute_with_tracking(
            "generate_code_changes", _generation_operation
        )

    def make_code_changes(
        self, repo_path: str, changes_description: str
    ) -> Optional[List[str]]:
        """
        Apply the AI-generated code changes to the repository.

        Args:
            repo_path: Path to the repository
            changes_description: AI-generated description of changes

        Returns:
            List[str]: List of created file names, or None if failed
        """

        def _apply_changes_operation():
            self.log(f"Implementing AI-generated changes in: {repo_path}")

            # Parse the changes_description to extract file names and content
            file_pattern = r"FILE:\s*([^\n]+)\n```(?:python)?\n(.*?)```"
            matches = re.findall(file_pattern, changes_description, re.DOTALL)

            if not matches:
                # Fallback: if no structured format, create a default Python script
                self.log(
                    "No structured file format found. Creating default Python script..."
                )
                return self._create_fallback_script(repo_path, changes_description)

            # Create each file found in the structured format
            created_files = []
            for filename, content in matches:
                filename = filename.strip()
                content = content.strip()

                # Ensure the filename has proper extension
                if not filename.endswith(".py") and "." not in filename:
                    filename += ".py"

                filepath = os.path.join(repo_path, filename)

                try:
                    with open(filepath, "w") as f:
                        f.write(content)
                    created_files.append(filename)
                    self.log(f"✅ Created: {filename}")
                except Exception as e:
                    self.log(f"❌ Error creating {filename}: {e}", "error")

            if created_files:
                self.log(
                    f"🎉 Successfully created {len(created_files)} file(s): {', '.join(created_files)}"
                )
            else:
                self.log("⚠️ No files were created", "warning")

            # Update state
            current_files = self.get_state("created_files", [])
            current_files.extend(created_files)
            self.update_state("created_files", current_files)

            return created_files

        return self.execute_with_tracking("make_code_changes", _apply_changes_operation)

    def _create_fallback_script(
        self, repo_path: str, changes_description: str
    ) -> List[str]:
        """
        Create a fallback script when no structured format is found.

        Args:
            repo_path: Path to the repository
            changes_description: AI-generated description

        Returns:
            List[str]: List of created file names
        """
        script_content = self.extract_python_code_from_text(changes_description)

        if script_content:
            filename = "ai_generated_script.py"
            filepath = os.path.join(repo_path, filename)
            with open(filepath, "w") as f:
                f.write(script_content)
            self.log(f"✅ Created fallback script: {filename}")
            return [filename]
        else:
            # If no Python code found, create documentation
            changes_file = os.path.join(repo_path, "AI_SUGGESTED_CHANGES.md")
            with open(changes_file, "w") as f:
                f.write("# AI Suggested Changes\n\n")
                f.write(changes_description)
            self.log(f"📝 Changes documented in: AI_SUGGESTED_CHANGES.md")
            return ["AI_SUGGESTED_CHANGES.md"]

    def extract_python_code_from_text(self, text: str) -> str:
        """
        Extract Python code from text, looking for code blocks or Python-like content.

        Args:
            text: Text to extract code from

        Returns:
            str: Extracted Python code
        """
        # Look for Python code blocks
        python_blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
        if python_blocks:
            return python_blocks[0].strip()

        # Look for any code blocks
        code_blocks = re.findall(r"```\n(.*?)```", text, re.DOTALL)
        if code_blocks:
            # Check if it looks like Python code
            for block in code_blocks:
                if any(
                    keyword in block
                    for keyword in ["import", "def ", "class ", "from ", "print("]
                ):
                    return block.strip()

        # If no code blocks, try to extract Python-like content
        lines = text.split("\n")
        python_lines = []
        in_code_section = False

        for line in lines:
            # Start collecting if we see Python keywords
            if any(
                keyword in line
                for keyword in ["import ", "from ", "def ", "class ", "if __name__"]
            ):
                in_code_section = True

            if in_code_section:
                python_lines.append(line)

        if python_lines:
            code = "\n".join(python_lines)
            # Basic validation - should have imports or function definitions
            if "import" in code or "def " in code:
                return code

        return ""

    def analyze_code_quality(self, code: str) -> Dict[str, any]:
        """
        Analyze the quality of generated code.

        Args:
            code: Code to analyze

        Returns:
            dict: Code quality metrics
        """

        def _analysis_operation():
            metrics = {
                "total_lines": len(code.split("\n")),
                "non_empty_lines": len(
                    [line for line in code.split("\n") if line.strip()]
                ),
                "has_imports": "import" in code,
                "has_functions": "def " in code,
                "has_classes": "class " in code,
                "has_main_guard": 'if __name__ == "__main__"' in code,
                "has_docstrings": '"""' in code or "'''" in code,
                "complexity_score": 0,
            }

            # Calculate complexity score
            complexity_indicators = [
                ("functions", code.count("def ")),
                ("classes", code.count("class ")),
                ("imports", code.count("import")),
                (
                    "conditionals",
                    code.count("if ") + code.count("elif ") + code.count("else:"),
                ),
                ("loops", code.count("for ") + code.count("while ")),
                ("try_except", code.count("try:") + code.count("except")),
            ]

            for indicator, count in complexity_indicators:
                metrics[f"{indicator}_count"] = count
                metrics["complexity_score"] += count

            # Quality assessment
            if metrics["complexity_score"] > 10:
                metrics["quality_level"] = "complex"
            elif metrics["complexity_score"] > 5:
                metrics["quality_level"] = "moderate"
            else:
                metrics["quality_level"] = "simple"

            return metrics

        return (
            self.execute_with_tracking("analyze_code_quality", _analysis_operation)
            or {}
        )

    def get_generation_history(self) -> List[Dict]:
        """
        Get the history of code generations.

        Returns:
            List[Dict]: List of generation records
        """
        return self.get_state("generated_code", [])

    def get_created_files(self) -> List[str]:
        """
        Get the list of files created by this agent.

        Returns:
            List[str]: List of created file names
        """
        return self.get_state("created_files", [])

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the AI Generator Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "generate": self.generate_code_changes,
            "apply": self.make_code_changes,
            "extract": self.extract_python_code_from_text,
            "analyze": self.analyze_code_quality,
            "history": self.get_generation_history,
            "files": self.get_created_files,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
