import os

def read_lines_from_file(file_path):
    """
    Read lines from a file
    
    :param file_path: Path to the file
    :return: List of lines
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        # Read lines, strip whitespace, and ignore empty lines
        lines = [line.strip() for line in file.readlines() if line.strip()]
    return lines

