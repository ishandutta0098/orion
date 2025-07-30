import os
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def generate_code_changes(prompt: str, repo_path: str) -> str:
    """Generate code changes for the repository based on the prompt."""
    # Use ChatOpenAI instead of deprecated OpenAI
    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0.1  # Specify the model explicitly
    )

    # Create proper prompt template
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
                "Please provide the complete code files needed to accomplish this task. "
                "Include proper imports, error handling, and documentation.",
            ),
        ]
    )

    # Use the modern approach instead of deprecated LLMChain
    chain = template | llm | StrOutputParser()

    return chain.invoke({"prompt": prompt, "repo_path": repo_path})


def make_code_changes(repo_path: str, changes_description: str) -> list:
    """Make the actual code changes to the repository.

    Args:
        repo_path: Path to the repository
        changes_description: AI-generated description of changes

    Returns:
        list: List of created file names
    """
    print(f"Implementing AI-generated changes in: {repo_path}")

    # Parse the changes_description to extract file names and content
    import re

    # Find all FILE: patterns followed by code blocks
    file_pattern = r"FILE:\s*([^\n]+)\n```(?:python)?\n(.*?)```"
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
            return [filename]
        else:
            # If no Python code found, create documentation
            changes_file = os.path.join(repo_path, "AI_SUGGESTED_CHANGES.md")
            with open(changes_file, "w") as f:
                f.write("# AI Suggested Changes\n\n")
                f.write(changes_description)
            print(f"📝 Changes documented in: AI_SUGGESTED_CHANGES.md")
            return ["AI_SUGGESTED_CHANGES.md"]

    # Create each file found in the structured format
    created_files = []
    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()

        # Ensure the filename has proper extension
        if not filename.endswith(".py") and not "." in filename:
            filename += ".py"

        filepath = os.path.join(repo_path, filename)

        try:
            with open(filepath, "w") as f:
                f.write(content)
            created_files.append(filename)
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")

    if created_files:
        print(
            f"\n🎉 Successfully created {len(created_files)} file(s): {', '.join(created_files)}"
        )
    else:
        print("⚠️ No files were created")

    return created_files


def extract_python_code_from_text(text: str) -> str:
    """Extract Python code from text, looking for code blocks or Python-like content."""
    import re

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
