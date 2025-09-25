import ast
import os
import subprocess
from typing import Optional

from openai import OpenAI


def _extract_docstring(file_path: str) -> Optional[str]:
    """Extract the top-level docstring from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        docstring = ast.get_docstring(tree)
        if docstring:
            first_line = docstring.strip().splitlines()[0]
            return first_line
    except Exception:
        pass
    return None


def _summarize_repository(repo_path: str) -> str:
    """Generate a simple summary of the repository's Python files."""
    lines = []
    for root, _, files in os.walk(repo_path):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                rel_path = os.path.relpath(path, repo_path)
                doc = _extract_docstring(path)
                if doc:
                    lines.append(f"{rel_path}: {doc}")
                else:
                    lines.append(f"{rel_path}: (no docstring)")
    if not lines:
        return "No Python files found in repository."
    return "\n".join(sorted(lines))


def explain_repository(
    repo_url: str, workdir: str, branch: Optional[str] = None
) -> str:
    """Clone a repository and generate an OpenAI-powered explanation.

    Returns the explanation string so it can be consumed by callers
    (e.g., the Discord bot) in addition to being printed to the
    terminal.
    """
    repo_name = os.path.splitext(os.path.basename(repo_url.rstrip("/")))[0]
    repo_path = os.path.join(workdir, repo_name)

    if not os.path.exists(repo_path):
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
    if branch:
        subprocess.run(["git", "fetch"], cwd=repo_path, check=True)
        subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True)

    summary = _summarize_repository(repo_path)

    prompt = (
        "You are an expert software engineer. Given the following summary of a "
        "Python repository, provide a clear and detailed explanation of the "
        "codebase, describing the purpose of each module and how they work together.\n\n"
        f"Repository summary:\n{summary}"
    )

    explanation = None
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = response.choices[0].message.content.strip()
    except Exception as e:
        explanation = (
            f"Failed to generate explanation via OpenAI API: {e}\n" f"\n{summary}"
        )

    print(f"\n📚 Codebase overview for {repo_name} (branch: {branch or 'default'})")
    print("=" * 60)
    print(explanation)

    return explanation
