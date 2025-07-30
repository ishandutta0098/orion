import os
import platform
import subprocess


def create_virtual_environment(repo_path: str) -> str:
    """Create a virtual environment for the repository.

    Args:
        repo_path: Path to the repository

    Returns:
        str: Path to the virtual environment
    """
    venv_path = os.path.join(repo_path, ".venv")

    try:
        if os.path.exists(venv_path):
            print("🔄 Virtual environment already exists, using existing one")
            return venv_path

        print("🐍 Creating virtual environment...")
        subprocess.run(["python", "-m", "venv", venv_path], check=True, cwd=repo_path)
        print("✅ Virtual environment created successfully")
        return venv_path

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        raise


def get_venv_python(venv_path: str) -> str:
    """Get the path to the Python executable in the virtual environment.

    Args:
        venv_path: Path to the virtual environment

    Returns:
        str: Path to the Python executable
    """
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")


def install_dependencies(repo_path: str, venv_python: str) -> bool:
    """Install dependencies from requirements.txt or detect and install common ones.

    Args:
        repo_path: Path to the repository
        venv_python: Path to the virtual environment Python executable

    Returns:
        bool: True if installation was successful
    """
    try:
        # First, upgrade pip
        print("📦 Upgrading pip...")
        subprocess.run(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            cwd=repo_path,
            capture_output=True,
        )

        # Check for requirements.txt
        requirements_file = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements_file):
            print("📋 Installing dependencies from requirements.txt...")
            subprocess.run(
                [venv_python, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                cwd=repo_path,
            )
            print("✅ Dependencies installed from requirements.txt")
            return True

        # If no requirements.txt, install common dependencies for AI/ML projects
        print("📦 No requirements.txt found, installing common dependencies...")
        common_deps = ["torch", "transformers", "pillow", "numpy", "requests"]

        for dep in common_deps:
            try:
                print(f"  Installing {dep}...")
                subprocess.run(
                    [venv_python, "-m", "pip", "install", dep],
                    check=True,
                    cwd=repo_path,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                print(f"  ⚠️ Failed to install {dep}, skipping...")

        print("✅ Common dependencies installed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_requirements_file(repo_path: str, venv_python: str) -> None:
    """Create or update requirements.txt with installed packages.

    Args:
        repo_path: Path to the repository
        venv_python: Path to the virtual environment Python executable
    """
    try:
        print("📝 Generating requirements.txt...")
        result = subprocess.run(
            [venv_python, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path,
        )

        requirements_path = os.path.join(repo_path, "requirements.txt")
        with open(requirements_path, "w") as f:
            f.write(result.stdout)

        print("✅ requirements.txt created/updated")

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Could not generate requirements.txt: {e}")
