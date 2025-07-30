import io
import os
import subprocess
import tempfile


def test_generated_code(repo_path: str, venv_python: str, created_files: list) -> bool:
    """Test the generated code to ensure it runs without errors.

    Args:
        repo_path: Path to the repository
        venv_python: Path to the virtual environment Python executable
        created_files: List of files that were created

    Returns:
        bool: True if all tests passed
    """
    if not created_files:
        print("⚠️ No files to test")
        return True

    print("🧪 Testing generated code...")

    all_tests_passed = True

    for filename in created_files:
        if not filename.endswith(".py"):
            continue

        filepath = os.path.join(repo_path, filename)
        if not os.path.exists(filepath):
            continue

        try:
            print(f"  Testing {filename}...")

            # First, check syntax by compiling
            with open(filepath, "r") as f:
                code = f.read()

            try:
                compile(code, filepath, "exec")
                print(f"  ✅ {filename} - Syntax OK")
            except SyntaxError as e:
                print(f"  ❌ {filename} - Syntax Error: {e}")
                all_tests_passed = False
                continue

            # Create a test wrapper script with dummy inputs
            test_success = create_and_run_test_wrapper(repo_path, filename, venv_python)

            if test_success:
                print(f"  ✅ {filename} - Execution OK")
            else:
                print(f"  ❌ {filename} - Execution failed")
                all_tests_passed = False

        except Exception as e:
            print(f"  ❌ {filename} - Test failed: {e}")
            all_tests_passed = False

    if all_tests_passed:
        print("✅ All code tests passed")
    else:
        print("❌ Some tests failed")

    return all_tests_passed


def create_and_run_test_wrapper(
    repo_path: str, filename: str, venv_python: str
) -> bool:
    """Create a test wrapper script that provides dummy inputs and runs the target script.

    Args:
        repo_path: Path to the repository
        filename: Name of the file to test
        venv_python: Path to the virtual environment Python executable

    Returns:
        bool: True if execution was successful
    """
    try:
        # Read the original file to analyze what it needs
        filepath = os.path.join(repo_path, filename)
        with open(filepath, "r") as f:
            code = f.read()

        # Create a test wrapper script
        test_wrapper_content = generate_test_wrapper(code, filename)

        # Write the test wrapper
        test_wrapper_path = os.path.join(repo_path, f"test_{filename}")
        with open(test_wrapper_path, "w") as f:
            f.write(test_wrapper_content)

        # Run the test wrapper
        try:
            result = subprocess.run(
                [venv_python, f"test_{filename}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
            )

            # Clean up the test wrapper
            os.remove(test_wrapper_path)

            if result.returncode == 0:
                if result.stdout:
                    print(f"    Output: {result.stdout[:200]}...")
                return True
            else:
                print(f"    ❌ Exit code: {result.returncode}")
                if result.stderr:
                    print(f"    Error: {result.stderr[:300]}...")
                if result.stdout:
                    print(f"    Output: {result.stdout[:200]}...")
                return False

        except subprocess.TimeoutExpired:
            print(f"    ❌ Execution timeout (60s)")
            # Clean up the test wrapper
            try:
                os.remove(test_wrapper_path)
            except:
                pass
            return False
        except Exception as e:
            print(f"    ❌ Execution error: {e}")
            # Clean up the test wrapper
            try:
                os.remove(test_wrapper_path)
            except:
                pass
            return False

    except Exception as e:
        print(f"    ❌ Test wrapper creation failed: {e}")
        return False


def generate_test_wrapper(code: str, filename: str) -> str:
    """Generate a test wrapper script that provides dummy inputs and handles common scenarios.

    Args:
        code: The original code content
        filename: Name of the original file

    Returns:
        str: Test wrapper script content
    """
    # Analyze the code to determine what kind of dummy inputs we need
    needs_image = any(
        keyword in code.lower()
        for keyword in ["image", "pil", "cv2", "pillow", "imread"]
    )
    needs_text = any(keyword in code.lower() for keyword in ["text", "input(", "clip"])
    needs_file_path = "file" in code.lower() and any(
        keyword in code for keyword in ["open(", "load", "read"]
    )
    has_main_guard = 'if __name__ == "__main__"' in code

    wrapper = f'''#!/usr/bin/env python3
"""
Test wrapper for {filename}
This script provides dummy inputs and tests the execution.
"""

import sys
import os
import tempfile
import io
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, '.')

def create_dummy_image():
    """Create a dummy image for testing."""
    try:
        from PIL import Image
        import numpy as np
        # Create a small dummy image
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        return dummy_img
    except ImportError:
        return None

def create_dummy_file():
    """Create a dummy file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    temp_file.write("This is a dummy file for testing purposes.\\n")
    temp_file.write("It contains sample text content.\\n")
    temp_file.close()
    return temp_file.name

def mock_input_function(prompt=""):
    """Mock input function that returns dummy values."""
    if 'image' in prompt.lower() or 'file' in prompt.lower():
        return create_dummy_file()
    elif 'text' in prompt.lower():
        return "This is a sample text for testing"
    else:
        return "dummy_input"

def main():
    """Run the test with proper mocking and error handling."""
    print(f"🧪 Testing {filename}...")
    
    # Prepare dummy data
    dummy_inputs = ["dummy_input", "test", "sample", create_dummy_file()]
    input_counter = 0
    
    def mock_input_with_counter(prompt=""):
        nonlocal input_counter
        if input_counter < len(dummy_inputs):
            result = dummy_inputs[input_counter]
            input_counter += 1
            return str(result)
        return mock_input_function(prompt)
    
    # Mock various functions that might cause issues
    mocks = {
        'input': mock_input_with_counter,
        'open': lambda *args, **kwargs: open(*args, **kwargs) if len(args) > 0 and os.path.exists(args[0]) else io.StringIO("dummy content"),
    }
    
    # Additional mocks for image processing
    if needs_image:
        try:
            from PIL import Image
            dummy_image = create_dummy_image()
            if dummy_image:
                Image.open = lambda *args, **kwargs: dummy_image
        except ImportError:
            pass
    
    try:
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        captured_output = io.StringIO()
        captured_errors = io.StringIO()
        
        sys.stdout = captured_output
        sys.stderr = captured_errors
        
        # Mock input and other problematic functions
        with patch('builtins.input', side_effect=mock_input_with_counter):
'''

    # Add the import and execution of the original module
    module_name = filename.replace(".py", "")

    if has_main_guard:
        # If the script has a main guard, we can import it safely
        wrapper += f"""
            # Import and run the module
            import {module_name}
            
            # If there's a main function, try to call it
            if hasattr({module_name}, 'main'):
                {module_name}.main()
            elif hasattr({module_name}, 'run'):
                {module_name}.run()
"""
    else:
        # If no main guard, execute the file directly but carefully
        wrapper += f"""
            # Execute the file content
            with open('{filename}', 'r') as f:
                code_content = f.read()
            
            # Execute in a controlled environment
            exec(code_content, {{'__name__': '__main__'}})
"""

    wrapper += f"""
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Check for any errors
        error_output = captured_errors.getvalue()
        if error_output and ('error' in error_output.lower() or 'exception' in error_output.lower()):
            print(f"❌ Errors detected in output:")
            print(error_output[:500])
            return False
        
        # Print captured output (truncated)
        output = captured_output.getvalue()
        if output:
            print(f"✅ Script executed successfully. Output:")
            print(output[:300] + "..." if len(output) > 300 else output)
        else:
            print(f"✅ Script executed successfully (no output)")
        
        return True
        
    except Exception as e:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        print(f"❌ Execution failed: {{type(e).__name__}}: {{e}}")
        return False
    
    finally:
        # Clean up any temporary files
        for dummy_input in dummy_inputs:
            if isinstance(dummy_input, str) and os.path.exists(dummy_input) and dummy_input.startswith('/tmp'):
                try:
                    os.unlink(dummy_input)
                except:
                    pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""

    return wrapper
