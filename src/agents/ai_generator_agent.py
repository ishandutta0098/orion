"""
AI Generator Agent for Orion AI Agent System

This agent handles AI-powered code generation using LangChain and GPT-5.
Simplified for GPT-5 only usage with best practices integration.
"""

import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class CodeGenerationResponse(BaseModel):
    """Structured response for code generation."""

    success: bool = Field(description="Whether the generation was successful")
    files: List[Dict[str, str]] = Field(
        description="Generated files with name and content"
    )
    modifications: List[Dict[str, str]] = Field(
        description="File modifications with target and changes", default=[]
    )
    reasoning: str = Field(
        description="Step-by-step explanation of the approach and decisions"
    )
    dependencies: List[str] = Field(description="Required dependencies", default=[])
    next_steps: List[str] = Field(description="Recommended next steps", default=[])
    confidence: float = Field(
        description="Confidence score (0-1) for the generated solution", default=0.9
    )


class AIGeneratorAgent(BaseAgent):
    """
    Agent responsible for AI-powered code generation using GPT-5.

    Features:
    - GPT-5 powered code generation with advanced reasoning
    - Structured outputs with validation using Pydantic models
    - Enhanced prompt engineering for better results
    - File creation and modification capabilities
    - Code quality analysis and validation
    """

    def __init__(
        self, model: str = "gpt-5-mini", temperature: float = 1.0, debug: bool = False
    ):
        """https://docs.google.com/presentation/d/1p-GZmQFdUvU00q6jTyPJHyPhVsP783_NFlPHqjvOzgU/edit?usp=sharing
        Initialize the AI Generator Agent with GPT-5.

        Args:
            model: GPT-5 model to use (gpt-5, gpt-5-mini, gpt-5-nano, or gpt-5-chat)
            temperature: Temperature for generation (0.1 for deterministic code)
            debug: Whether to enable debug mode
        """
        super().__init__("AIGenerator", debug)
        self.model = model
        self.temperature = temperature

        # Validate GPT-5 model
        if not model.startswith("gpt-5"):
            self.log(
                f"⚠️ Warning: {model} is not a GPT-5 model. Consider using gpt-5-mini for best results."
            )

        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=32768,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.update_state("model", model)
        self.update_state("temperature", temperature)
        self.update_state("generated_code", [])
        self.update_state("created_files", [])
        self.update_state("modified_files", [])

    def generate_code_changes(
        self, prompt: str, repo_path: str, context: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate code changes using GPT-5.

        Args:
            prompt: Task description for the AI
            repo_path: Path to the repository
            context: Additional context for generation

        Returns:
            str: Generated code changes with reasoning, or None if failed
        """

        def _generation_operation():
            # Enhanced prompt template for GPT-5
            template = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert software architect using GPT-5's advanced capabilities.

CORE COMPETENCIES:
- Software architecture and design patterns
- Modern development practices and frameworks  
- Code quality, security, and performance optimization
- Cross-platform and cloud-native development

OUTPUT REQUIREMENTS:
You MUST respond with valid JSON in this exact structure:
{{
  "success": true,
  "files": [
    {{"name": "filename.py", "content": "complete production-ready code"}},
    {{"name": "requirements.txt", "content": "package==version\\npackage2==version"}}
  ],
  "modifications": [
    {{"target": "existing_file.py", "changes": "specific changes to make"}}
  ],
  "reasoning": "Detailed step-by-step analysis of the problem, solution approach, design decisions, and trade-offs considered",
  "dependencies": ["package1", "package2"],
  "next_steps": ["step 1", "step 2"],
  "confidence": 0.95
}}

REASONING PROCESS:
1. ANALYZE: Break down requirements and constraints
2. DESIGN: Plan architecture and component interactions  
3. IMPLEMENT: Generate production-ready code with best practices
4. VALIDATE: Consider edge cases, security, and performance

QUALITY STANDARDS:
- Complete, runnable code with all imports
- Comprehensive error handling and logging
- Type hints and detailed Google-style docstrings
- Security best practices and input validation
- Performance optimization and resource management""",
                    ),
                    (
                        "user",
                        """DEVELOPMENT TASK:
Repository: {repo_path}
Task: {prompt}

CONTEXT:
{context}

REQUIREMENTS:
Generate a complete, production-ready solution that follows best practices.
Include detailed reasoning about your approach and design decisions.
Consider scalability, maintainability, and security in your solution.""",
                    ),
                ]
            )

            # Use structured output parser
            json_parser = JsonOutputParser(pydantic_object=CodeGenerationResponse)
            chain = template | self.llm | json_parser

            # Prepare context
            context_str = self._build_context(context, repo_path)

            self.log(f"🚀 Generating with GPT-5 model: {self.model}")

            try:
                result = chain.invoke(
                    {
                        "prompt": prompt,
                        "repo_path": repo_path,
                        "context": context_str,
                    }
                )

                # Format result for output
                if isinstance(result, dict):
                    formatted_result = self._format_structured_result(result)
                else:
                    formatted_result = str(result)

                # Update state
                generation_info = {
                    "prompt": prompt,
                    "repo_path": repo_path,
                    "context": context,
                    "result": result,
                    "formatted_result": formatted_result,
                    "timestamp": time.time(),
                    "model": self.model,
                    "success": (
                        result.get("success", False)
                        if isinstance(result, dict)
                        else True
                    ),
                    "reasoning": (
                        result.get("reasoning", "") if isinstance(result, dict) else ""
                    ),
                    "confidence": (
                        result.get("confidence", 0.9)
                        if isinstance(result, dict)
                        else 0.9
                    ),
                }

                generated_code = self.get_state("generated_code", [])
                generated_code.append(generation_info)
                self.update_state("generated_code", generated_code)

                return formatted_result

            except Exception as e:
                self.log(f"❌ GPT-5 generation failed: {e}", "error")
                return self._fallback_generation(prompt, repo_path, context_str)

        return self.execute_with_tracking(
            "generate_code_changes", _generation_operation
        )

    def _build_context(self, context: Optional[Dict], repo_path: str) -> str:
        """Build context with repository analysis."""
        context_parts = []

        if context:
            for key, value in context.items():
                context_parts.append(f"- {key}: {value}")

        # Add repository context if available
        try:
            if os.path.exists(repo_path):
                files = []
                for root, _, filenames in os.walk(repo_path):
                    for filename in filenames[:10]:  # Limit to first 10 files
                        if filename.endswith(
                            (".py", ".js", ".ts", ".java", ".go", ".rs")
                        ):
                            rel_path = os.path.relpath(
                                os.path.join(root, filename), repo_path
                            )
                            files.append(rel_path)

                if files:
                    context_parts.append(f"- Existing code files: {', '.join(files)}")
        except Exception:
            pass  # Ignore errors in context building

        return (
            "\n".join(context_parts)
            if context_parts
            else "No additional context provided"
        )

    def _format_structured_result(self, result: Dict) -> str:
        """Format structured result back to expected string format."""
        formatted_parts = []

        # Add model and confidence information
        confidence = result.get("confidence", 0.9)
        formatted_parts.append(
            f"# GENERATED WITH GPT-5 ({self.model}) - Confidence: {confidence:.1%}\n"
        )

        # Add reasoning as comment
        if result.get("reasoning"):
            reasoning_lines = result["reasoning"].split("\n")
            formatted_reasoning = "\n# ".join(["REASONING:"] + reasoning_lines)
            formatted_parts.append(f"# {formatted_reasoning}\n")

        # Format file creations
        for file_info in result.get("files", []):
            name = file_info.get("name", "unknown.py")
            content = file_info.get("content", "")
            formatted_parts.append(f"FILE: {name}\n```python\n{content}\n```\n")

        # Format modifications
        for mod_info in result.get("modifications", []):
            target = mod_info.get("target", "unknown.py")
            changes = mod_info.get("changes", "")
            formatted_parts.append(f"MODIFY: {target}\n```\n{changes}\n```\n")

        # Add dependencies and next steps as comments
        if result.get("dependencies"):
            deps = ", ".join(result["dependencies"])
            formatted_parts.append(f"# DEPENDENCIES: {deps}\n")

        if result.get("next_steps"):
            steps = "\n# ".join(result["next_steps"])
            formatted_parts.append(f"# NEXT STEPS:\n# {steps}\n")

        return "\n".join(formatted_parts)

    def _fallback_generation(
        self, prompt: str, repo_path: str, context_str: str
    ) -> str:
        """Fallback generation method using simpler approach."""
        self.log("🔄 Using fallback generation method...")

        fallback_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert Python developer using GPT-5. Generate complete, production-ready code files.

OUTPUT FORMAT:
For each file, use this EXACT format:

FILE: filename.py
```python
# Complete file content with imports, classes, functions
# Include proper docstrings and type hints
```

REQUIREMENTS:
- Complete, runnable code
- All necessary imports
- Google-style docstrings  
- Type hints
- Error handling
- Follow PEP 8""",
                ),
                (
                    "user",
                    "Repository: {repo_path}\nTask: {prompt}\nContext: {context}",
                ),
            ]
        )

        chain = fallback_template | self.llm | StrOutputParser()
        return chain.invoke(
            {
                "prompt": prompt,
                "repo_path": repo_path,
                "context": context_str,
            }
        )

    def make_code_changes(self, generated_code: str, repo_path: str) -> bool:
        """
        Apply generated code changes to the repository.

        Args:
            generated_code: Generated code string with FILE: and MODIFY: directives
            repo_path: Repository path

        Returns:
            bool: True if changes were applied successfully
        """
        try:
            self.log("📝 Applying generated code changes...")
            success = True

            # Parse the generated code for FILE: and MODIFY: directives
            lines = generated_code.split("\n")
            current_file = None
            current_content = []
            in_code_block = False

            for line in lines:
                if line.startswith("FILE: "):
                    # Save previous file if exists
                    if current_file and current_content:
                        success &= self._write_new_file(
                            repo_path, current_file, "\n".join(current_content)
                        )

                    # Start new file
                    current_file = line[6:].strip()
                    current_content = []
                    in_code_block = False

                elif line.startswith("MODIFY: "):
                    # Handle file modifications
                    target_file = line[8:].strip()
                    self.log(f"🔧 Modification needed for: {target_file}")

                elif line.startswith("```"):
                    in_code_block = not in_code_block
                    if not in_code_block and current_file:
                        # End of code block, save file
                        success &= self._write_new_file(
                            repo_path, current_file, "\n".join(current_content)
                        )
                        current_file = None
                        current_content = []

                elif in_code_block and current_file:
                    current_content.append(line)

            # Handle last file if exists
            if current_file and current_content:
                success &= self._write_new_file(
                    repo_path, current_file, "\n".join(current_content)
                )

            return success

        except Exception as e:
            self.log(f"❌ Failed to apply code changes: {e}", "error")
            return False

    def _write_new_file(self, repo_path: str, file_path: str, content: str) -> bool:
        """
        Write a new file to the repository.

        Args:
            repo_path: Repository path
            file_path: Relative file path
            content: File content

        Returns:
            bool: True if successful
        """
        try:
            full_path = os.path.join(repo_path, file_path)

            # Create directory if it doesn't exist
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.log(f"✅ Created file: {file_path}")

            # Track created file
            created_files = self.get_state("created_files", [])
            created_files.append(file_path)
            self.update_state("created_files", created_files)

            return True

        except Exception as e:
            self.log(f"❌ Failed to write file {file_path}: {e}", "error")
            return False

    def _write_modified_file(
        self, full_file_path: str, original_content: str, modified_content: str
    ) -> bool:
        """
        Write modified content to a file.

        Args:
            full_file_path: Full path to the file
            original_content: Original file content
            modified_content: Modified file content

        Returns:
            bool: True if successful
        """
        try:
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            self.log(f"✅ Modified file: {full_file_path}")

            # Track modified file
            modified_files = self.get_state("modified_files", [])
            modified_files.append(
                {
                    "path": full_file_path,
                    "original_size": len(original_content),
                    "modified_size": len(modified_content),
                    "timestamp": time.time(),
                }
            )
            self.update_state("modified_files", modified_files)

            return True

        except Exception as e:
            self.log(f"❌ Failed to write modified file {full_file_path}: {e}", "error")
            return False

    def extract_python_code_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract Python code blocks from text.

        Args:
            text: Text containing code blocks

        Returns:
            List of dictionaries with filename and content
        """
        code_blocks = []
        lines = text.split("\n")
        current_file = None
        current_content = []
        in_code_block = False

        for line in lines:
            if line.startswith("FILE: "):
                current_file = line[6:].strip()
            elif line.startswith("```python") or line.startswith("```"):
                in_code_block = not in_code_block
                if not in_code_block and current_file:
                    code_blocks.append(
                        {
                            "filename": current_file,
                            "content": "\n".join(current_content),
                        }
                    )
                    current_content = []
                    current_file = None
            elif in_code_block:
                current_content.append(line)

        return code_blocks

    def analyze_code_quality(
        self, code: str, filename: str = "unknown.py"
    ) -> Dict[str, Any]:
        """
        Analyze code quality using basic metrics.

        Args:
            code: Code to analyze
            filename: Name of the file

        Returns:
            Dictionary with quality metrics
        """
        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "filename": filename,
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "has_docstrings": '"""' in code or "'''" in code,
            "has_type_hints": "->" in code or ": " in code,
            "has_imports": any(
                line.strip().startswith(("import ", "from ")) for line in lines
            ),
            "complexity_estimate": len(
                [
                    line
                    for line in lines
                    if any(
                        keyword in line
                        for keyword in ["if ", "for ", "while ", "def ", "class "]
                    )
                ]
            ),
        }

    def get_generation_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of code generations.

        Returns:
            List of generation records
        """
        return self.get_state("generated_code", [])

    def get_created_files(self) -> List[str]:
        """
        Get list of files created by this agent.

        Returns:
            List of created file paths
        """
        return self.get_state("created_files", [])

    def get_modified_files(self) -> List[Dict[str, Any]]:
        """
        Get list of files modified by this agent.

        Returns:
            List of modification records
        """
        return self.get_state("modified_files", [])

    def generate_code_with_context(
        self,
        prompt: str,
        repo_path: str,
        repository_context: Optional[Dict] = None,
        task_classification: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Generate code with additional context using GPT-5.

        Args:
            prompt: Task description
            repo_path: Repository path
            repository_context: Repository scan context
            task_classification: Task classification context

        Returns:
            str: Generated code or None if failed
        """
        # Combine both contexts into a single context dictionary
        combined_context = {}
        if repository_context:
            combined_context.update(repository_context)
        if task_classification:
            combined_context.update(task_classification)

        return self.generate_code_changes(
            prompt, repo_path, combined_context if combined_context else None
        )

    def modify_existing_file(
        self,
        repo_path: str,
        file_path: str,
        modification_description: str,
        file_content: Optional[str] = None,
    ) -> Optional[str]:
        """
        Modify an existing file with targeted changes using GPT-5.

        Args:
            repo_path: Repository path
            file_path: Path to file to modify
            modification_description: Description of changes to make
            file_content: Optional file content (will read from disk if not provided)

        Returns:
            str: Modified file content or None if failed
        """
        try:
            self.log(f"🔧 Modifying file with GPT-5: {file_path}")

            # Construct full file path
            if os.path.isabs(file_path):
                full_file_path = file_path
            else:
                full_file_path = os.path.join(repo_path, file_path)

            # Read existing content
            if file_content is None:
                if not os.path.exists(full_file_path):
                    self.log(f"❌ File not found: {full_file_path}", "error")
                    return None

                with open(full_file_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            else:
                existing_content = file_content

            self.log(f"📄 Original file content ({len(existing_content)} chars)")

            # Use GPT-5 for precise modification
            modification_template = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a precise code editor using GPT-5's advanced capabilities.

TASK: Modify code files with surgical precision while preserving all existing functionality.

CRITICAL RULES:
- Make ONLY the requested change - do not refactor, reorganize, or "improve" other code
- Preserve ALL existing imports, comments, formatting, and structure
- Maintain the exact same file structure and organization
- Keep all existing functionality intact
- If changing a value, change ONLY that specific value
- If modifying a function, change ONLY what was requested

OUTPUT: Return the complete modified file content with only the minimal necessary change applied.""",
                    ),
                    (
                        "user",
                        """MODIFICATION REQUEST: {modification_description}

ORIGINAL FILE CONTENT:
```
{existing_content}
```

Apply the requested change with surgical precision, keeping everything else exactly the same:""",
                    ),
                ]
            )

            modification_chain = modification_template | self.llm | StrOutputParser()
            modified_content = modification_chain.invoke(
                {
                    "existing_content": existing_content,
                    "modification_description": modification_description,
                }
            )

            # Clean up the response (remove code block markers if present)
            modified_content = modified_content.strip()
            if modified_content.startswith("```"):
                lines = modified_content.split("\n")
                if len(lines) > 2:
                    modified_content = "\n".join(lines[1:-1])

            # Verify that the change isn't too drastic
            from difflib import SequenceMatcher

            similarity = SequenceMatcher(
                None, existing_content, modified_content
            ).ratio()

            if similarity < 0.5:  # If less than 50% similar, it's probably wrong
                self.log(
                    f"❌ Modification too drastic (similarity: {similarity:.2f}), rejecting",
                    "error",
                )
                return None

            self.log(f"✅ GPT-5 modification applied (similarity: {similarity:.2f})")

            # Write the modified content
            self._write_modified_file(
                full_file_path, existing_content, modified_content
            )
            return modified_content

        except Exception as e:
            self.log(f"❌ GPT-5 modification failed: {e}", "error")
            return None

    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the current GPT-5 model.

        Returns:
            Dict: Model information
        """
        return {
            "model": self.model,
            "is_gpt5": self.model.startswith("gpt-5"),
            "temperature": self.temperature,
            "max_tokens": 32768,
            "supports_structured_output": True,
            "supports_reasoning": True,
            "context_window": 272000 if self.model.startswith("gpt-5") else 128000,
        }

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
            "generate_with_context": self.generate_code_with_context,
            "apply": self.make_code_changes,
            "modify": self.modify_existing_file,
            "extract": self.extract_python_code_from_text,
            "analyze": self.analyze_code_quality,
            "history": self.get_generation_history,
            "files": self.get_created_files,
            "modified_files": self.get_modified_files,
            "model_info": self.get_model_info,
        }

        if action not in action_map:
            self.log(
                f"❌ Unknown action: {action}. Available actions: {list(action_map.keys())}",
                "error",
            )
            return None

        try:
            self.log(f"🎯 Executing action: {action}")
            result = action_map[action](**kwargs)

            if result is not None:
                self.log(f"✅ Action {action} completed successfully")
            else:
                self.log(f"⚠️ Action {action} returned None", "warning")

            return result
        except Exception as e:
            self.log(f"❌ Error executing action {action}: {e}", "error")
            return None
