filepath = "../usr/local/lib/python3.14/site-packages/djongo/models/fields.py"

with open(filepath, "r") as file:
    # Read the contents of the file
    file_contents = file.read()

file_contents = file_contents.replace(
    "def from_db_value(self, value, expression, connection, context):",
    "def from_db_value(self, value, expression, connection, context=None):",
)

with open(filepath, "w") as file:
    file.write(file_contents)
