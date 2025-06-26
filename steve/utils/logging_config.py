import logging
from datetime import datetime
from pathlib import Path


def setup_logging(level=logging.INFO):
    """
    Set up centralized logging configuration for the bot.

    Args:
        level: Logging level (default: logging.INFO)
    """
    # Get the project root directory (sbi-discord-bot folder)
    project_root = Path(__file__).parent.parent.parent

    # Ensure logs directory exists in project root
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log filename with current date
    log_filename = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(),
        ],
        force=True,  # Override any existing configuration
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging configuration when module is imported
setup_logging()
