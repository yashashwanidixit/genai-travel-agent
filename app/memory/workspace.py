from typing import Dict, Any, Optional


class WorkspaceMemory:
    """Working scratchpad memory for active multi-agent planning and intermediate state synthesis."""

    def __init__(self):
        self._workspace: Dict[str, Dict[str, Any]] = {}

    def set_value(self, plan_id: str, key: str, value: Any):
        if plan_id not in self._workspace:
            self._workspace[plan_id] = {}
        self._workspace[plan_id][key] = value

    def get_value(self, plan_id: str, key: str, default: Any = None) -> Any:
        return self._workspace.get(plan_id, {}).get(key, default)

    def get_all(self, plan_id: str) -> Dict[str, Any]:
        return self._workspace.get(plan_id, {}).copy()

    def clear(self, plan_id: str):
        if plan_id in self._workspace:
            del self._workspace[plan_id]
