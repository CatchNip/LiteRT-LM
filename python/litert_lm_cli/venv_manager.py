# Copyright 2026 The ODML Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Virtual environment manager for LiteRT-LM."""

import os
import subprocess
import sys

# The dir for the virtual environment managed by this CLI. This dir won't be
# used if there is an active virtual environment.
_SELF_MANAGED_VENV_DIR = os.path.expanduser("~/.litert-lm/.venv")

# The directory for the virtual environment. It prioritizes the active virtual
# environment if available (VIRTUAL_ENV or sys.prefix) over the "self-managed"
# virtual environment.
VENV_DIR = os.environ.get(
    "VIRTUAL_ENV",
    sys.prefix if sys.prefix != sys.base_prefix else _SELF_MANAGED_VENV_DIR,
)

PYTHON_BIN = os.path.join(VENV_DIR, "bin", "python")
PIP_BIN = os.path.join(VENV_DIR, "bin", "pip")
LITERT_TORCH_BIN = os.path.join(VENV_DIR, "bin", "litert-torch")
UV_BIN = os.path.join(VENV_DIR, "bin", "uv")


def ensure_venv():
  """Ensures that the virtual environment directory exists."""
  if os.path.exists(VENV_DIR):
    return

  if VENV_DIR != _SELF_MANAGED_VENV_DIR:
    # Note this should never happen.
    raise RuntimeError(f"Virtual environment directory not found: {VENV_DIR}")

  print(f"Creating virtual environment in {VENV_DIR}...")
  os.makedirs(os.path.dirname(VENV_DIR), exist_ok=True)
  python_exe = sys.executable or "python3"
  subprocess.run([python_exe, "-m", "venv", VENV_DIR], check=True)


def recreate_venv_if_self_managed():
  """Deletes and re-creates the virtual environment if it is self-managed.

  This ensures we are using the latest litert-torch-nightly. Since uv has local
  cache, if the version has been downloaded before, it will be very fast.
  """
  if VENV_DIR != _SELF_MANAGED_VENV_DIR:
    # Only recreate if it's the default venv managed by the CLI.
    return

  if os.path.exists(VENV_DIR):
    import shutil

    print(f"Deleting virtual environment in {VENV_DIR}...")
    shutil.rmtree(VENV_DIR)

  ensure_venv()


def ensure_binary(binary_path):
  """Ensures the binary exists, or installs it if using the default venv."""
  if os.path.exists(binary_path):
    return

  if VENV_DIR != _SELF_MANAGED_VENV_DIR:
    # This might happens if user manually uninstall the package to break the
    # dependency.
    raise RuntimeError(
        "Required binary not found in the active virtual environment:"
        f" {VENV_DIR}. Binary path: {binary_path}. Please install the"
        " corresponding package manually."
    )
  else:
    # If the venv is _SELF_MANAGED_VENV_DIR (~/.litert-lm/.venv) managed by the CLI,
    # then attempt to install the required dependencies.
    pass

  ensure_venv()

  if binary_path == PIP_BIN:
    print("Ensuring pip is installed...")
    subprocess.run(
        [
            PYTHON_BIN,
            "-m",
            "ensurepip",
            "--default-pip",
        ],
        check=True,
    )
  elif binary_path == UV_BIN:
    ensure_binary(PIP_BIN)
    print("Installing uv into the virtual environment...")
    subprocess.run(
        [
            PIP_BIN,
            "install",
            "uv",
            "-i",
            "https://pypi.org/simple",
        ],
        check=True,
    )
  elif binary_path == LITERT_TORCH_BIN:
    ensure_binary(UV_BIN)
    print("Installing litert-torch with uv...")
    subprocess.run(
        [
            UV_BIN,
            "pip",
            "install",
            "-i",
            "https://pypi.org/simple",
            "litert-torch-nightly",
            "--python",
            PYTHON_BIN,
        ],
        check=True,
    )
