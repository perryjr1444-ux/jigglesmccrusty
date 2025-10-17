import yaml
import jinja2
from pathlib import Path


class Commander:
    """
    Loads a playbook YAML, renders it with a context dict,
    validates that every task has a unique name, and returns a dict
    compatible with Orchestrator.run_playbook().
    """

    def __init__(self, playbook_dir: Path):
        self.dir = playbook_dir
        # Use StrictUndefined to catch errors in rendering, but handle them gracefully
        # to preserve task references like {{task_name.output.field}}
        self.jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)

    def load(self, playbook_id: str, context: dict) -> dict:
        pb_path = self.dir / f"{playbook_id}.yaml"
        raw = yaml.safe_load(pb_path.read_text())

        # Render every field that is a string (deep walk)
        rendered = self._render_recursive(raw, context)

        # Basic sanity checks
        tasks = rendered.get("tasks", {})
        if isinstance(tasks, dict):
            task_names = list(tasks.keys())
        else:
            task_names = tasks
        
        # Validate task uniqueness
        if len(task_names) != len(set(task_names)):
            raise ValueError("Duplicate task names in playbook")

        # Return a compact dict the orchestrator expects
        return {
            "playbook_id": rendered.get("id", playbook_id),
            "description": rendered.get("description", ""),
            "severity": rendered.get("severity", "medium"),
            "tags": rendered.get("tags", []),
            "tasks": tasks,
        }

    def _render_recursive(self, obj, ctx):
        if isinstance(obj, dict):
            return {k: self._render_recursive(v, ctx) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._render_recursive(i, ctx) for i in obj]
        if isinstance(obj, str):
            try:
                tmpl = self.jinja_env.from_string(obj)
                return tmpl.render(**ctx)
            except jinja2.UndefinedError:
                # Preserve template strings with undefined variables (e.g., task references)
                return obj
        return obj
