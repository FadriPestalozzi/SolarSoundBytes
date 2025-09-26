"""
Shared Utility Functions

Common utility functions used across multiple scripts in the data acquisition pipeline.
Includes path utilities, progress display, and other general-purpose functions.
"""

import os


def get_project_root() -> str:
    """Get the absolute path to the project root directory"""
    current_dir = os.path.dirname(__file__)
    
    # In Docker/deployment environment, check if we're in /app
    if os.path.exists("/app") and os.path.basename(os.getcwd()) != "SolarSoundBytes":
        # We're likely in a Docker container
        return "/app"
    
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


def get_db_path() -> str:
    """Get the path to the Twitter database (legacy function)"""
    return os.path.join(get_project_root(), "database", "db-twitter.db")

def get_twitter_db_path() -> str:
    """Get the path to the Twitter database"""
    return os.path.join(get_project_root(), "database", "db-twitter.db")

def get_news_db_path() -> str:
    """Get the path to the News database"""
    return os.path.join(get_project_root(), "database", "db-news-articles.db")


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """
    Generate a text-based progress bar string
    
    Args:
        current: Current progress value
        total: Total/maximum value
        width: Width of the progress bar in characters (default: 40)
        
    Returns:
        Formatted progress bar string with percentage
    """
    percent = current / total
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    return f"\r[{bar}] {current}/{total} ({percent:.1%})"


def ensure_directory_exists(path: str) -> None:
    """Ensure that a directory exists, creating it if necessary"""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_data_dir(subdir: str = "") -> str:
    """Get the path to a data subdirectory"""
    base_path = os.path.join(get_project_root(), "data")
    if subdir:
        return os.path.join(base_path, subdir)
    return base_path


def get_csv_data_dir() -> str:
    """Get the path to the CSV data directory"""
    return get_data_dir("csv")


def get_json_data_dir() -> str:
    """Get the path to the JSON data directory"""
    return get_data_dir("json")
