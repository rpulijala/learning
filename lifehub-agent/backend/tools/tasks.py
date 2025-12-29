"""Tasks tool - manages tasks in a local JSON file."""

import json
from pathlib import Path

from langchain_core.tools import tool

# Path to tasks.json in the state directory
TASKS_FILE = Path(__file__).parent.parent / "state" / "tasks.json"


def _load_tasks() -> list[dict]:
    """Load tasks from JSON file."""
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_tasks(tasks: list[dict]) -> None:
    """Save tasks to JSON file."""
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


@tool
def add_task(task: str) -> dict:
    """Add a new task to the task list.
    
    Args:
        task: The task description to add.
        
    Returns:
        A confirmation message with the task details.
    """
    tasks = _load_tasks()
    new_task = {
        "id": len(tasks) + 1,
        "task": task,
        "completed": False,
    }
    tasks.append(new_task)
    _save_tasks(tasks)
    
    return {
        "status": "success",
        "message": f"Task added successfully",
        "task": new_task,
        "total_tasks": len(tasks),
    }
