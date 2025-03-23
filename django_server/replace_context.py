import os
import re
import sys

import dotenv

dotenv.load_dotenv()

IS_DOCKER = os.getenv("DOCKER", "false").lower() == "true"

PYTHON_VERSION = "3.13"

if IS_DOCKER:
    # Get Python version from Dockerfile
    dockerfile_path = os.path.join(os.path.dirname(__file__), "Dockerfile")
    with open(dockerfile_path, "r") as dockerfile:
        dockerfile_contents = dockerfile.read()

    python_version_match = re.search(
        r"python(\d+\.\d+)", dockerfile_contents, re.IGNORECASE
    )
    if python_version_match:
        PYTHON_VERSION = python_version_match.group(1)


else:
    # Get Python version from the current virtual environment
    PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


filepath = (
    f"../usr/local/lib/python{PYTHON_VERSION}/site-packages/djongo/models/fields.py"
)

with open(filepath, "r") as file:
    file_contents = file.read()

file_contents = file_contents.replace(
    "def from_db_value(self, value, expression, connection, context):",
    "def from_db_value(self, value, expression, connection, context=None):",
)

with open(filepath, "w") as file:
    file.write(file_contents)
