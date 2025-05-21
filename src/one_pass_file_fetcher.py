import json
import subprocess
import os


def fetch_file_with_op(item_title: str) -> dict:
    try:
        vault_name: str = os.getenv("OP_VAULT")
        # Step 1: Get the item details to find the file ID
        cmd_get_item = [
            "op", "item", "get", item_title,
            "--vault", vault_name,
            "--format", "json"
        ]
        item_details = subprocess.check_output(cmd_get_item, text=True)
        item_data = json.loads(item_details)

        # Step 2: Locate the file within the item details
        if "files" not in item_data or not item_data["files"]:
            raise ValueError(f"No files found in the item '{item_title}'.")

        # Assuming the first file is needed
        file_id = item_data["files"][0]["id"]

        # Step 3: Use 'op read' to get the content of the file directly
        cmd_read_file = ["op", "read",
                         f"op://{vault_name}/{item_title}/{file_id}"]
        file_content = subprocess.check_output(cmd_read_file, text=True)

        # Step 4: Parse the file content as JSON
        file_json = json.loads(file_content)
        return file_json

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON content: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
