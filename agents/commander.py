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
        self.jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)

    def load(self, playbook_id: str, context: dict) -> dict:
        pb_path = self.dir / f"{playbook_id}.yaml"
        raw = yaml.safe_load(pb_path.read_text())

        # Render every field that is a string (deep walk)
        rendered = self._render_recursive(raw, context)

        # Basic sanity checks
        tasks = rendered["tasks"]
        if len(tasks) != len(set(tasks)):
            raise ValueError("Duplicate task names in playbook")

        # Return a compact dict the orchestrator expects
        return {
            "playbook_id": playbook_id,
            "tasks": tasks,
        }

    def _render_recursive(self, obj, ctx):
        if isinstance(obj, dict):
            return {k: self._render_recursive(v, ctx) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._render_recursive(i, ctx) for i in obj]
        if isinstance(obj, str):
            tmpl = self.jinja_env.from_string(obj)
            return tmpl.render(**ctx)
        return obj
