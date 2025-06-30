import os


def is_virtualenv_dir(path):
    """
    Returns True if the given directory looks like a Python virtual environment.
    """
    pyvenv_cfg = os.path.join(path, "pyvenv.cfg")
    bin_python = os.path.join(path, "bin", "python")
    scripts_python = os.path.join(path, "Scripts", "python.exe")

    if os.path.isfile(pyvenv_cfg):
        if os.path.isfile(bin_python) or os.path.isfile(scripts_python):
            return True
    return False

def get_python_file_paths(directory_path):
    """
    Recursively get .py files, skipping virtual environments.
    """
    python_files = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if not is_virtualenv_dir(os.path.join(root, d))]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    return python_files
