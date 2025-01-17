import sys
import os


def _set_paths():

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the target directory relative to the current script
    target_dir = os.path.join(current_dir, '../')
    # Add the target directory to sys.path
    sys.path.append(target_dir)
