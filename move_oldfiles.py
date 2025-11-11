import json
import os
import shutil
import time
from datetime import datetime, timedelta
import sys

# --- Utility Functions ---

def load_config(file_path):
    """
    Reads and loads the configuration from a JSON file.
    :param file_path: Path to the configuration JSON file.
    :return: A list of configuration dictionaries.
    """
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        return config.get('file_mover_config', [])
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return []

def get_age_threshold_timestamp(age_hours):
    """
    Calculates the POSIX timestamp for the age threshold.
    Files older than this timestamp will be moved/deleted.
    :param age_hours: The minimum age in hours.
    :return: POSIX timestamp (seconds since epoch).
    """
    # Calculate the timestamp for 'age_hours' ago
    age_limit = datetime.now() - timedelta(hours=age_hours)
    return age_limit.timestamp()

# --- Main Logic Functions ---

def move_old_files(source_path, target_path, age_threshold_hours):
    """
    Recursively finds and moves files older than the threshold from source to target,
    preserving the relative directory structure.
    :param source_path: The root directory to scan.
    :param target_path: The destination root directory.
    :param age_threshold_hours: The minimum age (in hours) to move a file.
    :return: None
    """
    
    print(f"\n--- MOVE PROCESS: {source_path} ---")
    print(f"Criterion: Older than {age_threshold_hours} hours")
    
    source_path = os.path.abspath(source_path)
    
    if not os.path.isdir(source_path):
        print(f"Warning: Source path does not exist or is not a directory: {source_path}")
        return

    age_limit_timestamp = get_age_threshold_timestamp(age_threshold_hours)
    moved_count = 0
    
    for root, _, files in os.walk(source_path):
        relative_path = os.path.relpath(root, source_path)
        destination_dir = os.path.join(target_path, relative_path)
        
        os.makedirs(destination_dir, exist_ok=True)
        
        for file_name in files:
            source_file_path = os.path.join(root, file_name)
            target_file_path = os.path.join(destination_dir, file_name)
            
            try:
                file_mtime = os.stat(source_file_path).st_mtime
                
                if file_mtime < age_limit_timestamp:
                    shutil.move(source_file_path, target_file_path)
                    moved_count += 1
                    print(f"  MOVED: {source_file_path} -> {target_file_path}")
                    
            except FileNotFoundError:
                print(f"  Skipping: File not found (concurrent modification?): {source_file_path}")
            except Exception as e:
                print(f"  Error moving {source_file_path}: {e}")
                
    print(f"Completed moving files. Total files moved: {moved_count}")
    
def delete_very_old_files(target_path, deletion_threshold_hours):
    """
    Recursively finds and deletes files in the target path that are older 
    than the specified deletion threshold.
    :param target_path: The root directory to scan for deletion.
    :param deletion_threshold_hours: The minimum age (in hours) to delete a file.
    :return: None
    """
    
    print(f"\n--- DELETION PROCESS: {target_path} ---")
    print(f"Criterion: Older than {deletion_threshold_hours} hours")
    
    target_path = os.path.abspath(target_path)
    
    if not os.path.isdir(target_path):
        print(f"Warning: Target path does not exist or is not a directory: {target_path}")
        return

    deletion_limit_timestamp = get_age_threshold_timestamp(deletion_threshold_hours)
    deleted_count = 0
    
    # os.walk is used to traverse directories recursively
    for root, dirs, files in os.walk(target_path, topdown=False): # topdown=False ensures we process subdirs first
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            try:
                file_mtime = os.stat(file_path).st_mtime
                
                if file_mtime < deletion_limit_timestamp:
                    # File is very old, delete it
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"  DELETED: {file_path}")
                    
            except FileNotFoundError:
                # File may have been deleted by another process, or deleted in the same loop iteration
                pass
            except Exception as e:
                print(f"  Error deleting {file_path}: {e}")
                
        # After processing files, check if the directory is empty and delete it
        # This handles the removal of empty directories after file deletion
        try:
            if not os.listdir(root) and root != target_path:
                os.rmdir(root)
                print(f"  REMOVED EMPTY DIRECTORY: {root}")
        except OSError as e:
            # Handles errors like directory being non-empty (e.g., other processes created files)
            pass
            
    print(f"Completed deleting files. Total files deleted: {deleted_count}")


# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python move_old_files.py <config_file_name.json>")
        sys.exit(1)
        
    CONFIG_FILE = sys.argv[1]
    
    configs = load_config(CONFIG_FILE)
    
    if configs:
        print(f"Starting scheduled file cleanup using config: {CONFIG_FILE}")
        
        for conf in configs:
            source_path = conf.get('source_path')
            target_path = conf.get('target_path')
            age_threshold_hours = conf.get('age_threshold_hours', 0)
            deletion_threshold_hours = conf.get('deletion_threshold_hours')
            
            if not source_path or not target_path:
                print("Skipping configuration: 'source_path' or 'target_path' missing.")
                continue

            # 1. MOVE old files from source to target
            move_old_files(source_path, target_path, age_threshold_hours)

            # 2. DELETE very old files from target
            # Only run deletion if 'deletion_threshold_hours' is provided in the config
            if deletion_threshold_hours is not None:
                delete_very_old_files(target_path, deletion_threshold_hours)
            else:
                print(f"\nSkipping deletion for {target_path}: 'deletion_threshold_hours' not configured.")
                
        print("\nScheduled file cleanup finished.")
    else:
        print("No valid configurations found. Exiting.")