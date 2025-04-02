import os
from pathlib import Path

# Get the current file's path
current_file_path = Path(__file__).resolve()

# Get the grand parent directory (shipments)
parent = str(current_file_path.parent.parent)

ALL_PICKLE_PATH = parent + "/all_pickle_files"
ALL_PICKLE_PATH_COPY = parent + "/all_pickle_files_copy"    