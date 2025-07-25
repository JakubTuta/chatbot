import os
import sys
import importlib.util

try:
    djongo_spec = importlib.util.find_spec('djongo')
    if djongo_spec and djongo_spec.origin:
        djongo_path = os.path.dirname(djongo_spec.origin)
        filepath = os.path.join(djongo_path, 'models', 'fields.py')
    else:
        raise ImportError("djongo package not found.")

except ImportError:
    print("Djongo is not installed. Skipping patch.")
    sys.exit(0)
except Exception as e:
    print(f"Could not find djongo path: {e}")
    sys.exit(1)


if not os.path.exists(filepath):
    print(f"File to patch does not exist: {filepath}")
    sys.exit(1)

with open(filepath, "r") as file:
    file_contents = file.read()

# Check if the patch is already applied
if "def from_db_value(self, value, expression, connection, context=None):" in file_contents:
    print("Patch already applied.")
    sys.exit(0)

file_contents = file_contents.replace(
    "def from_db_value(self, value, expression, connection, context):",
    "def from_db_value(self, value, expression, connection, context=None):",
)

try:
    with open(filepath, "w") as file:
        file.write(file_contents)
    print(f"Successfully patched {filepath}")
except Exception as e:
    print(f"Error writing to {filepath}: {e}")
    sys.exit(1)
