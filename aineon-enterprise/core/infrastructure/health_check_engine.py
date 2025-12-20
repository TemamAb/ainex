from typing import Callable, Any, Dict, List

class HealthCheckEngine:
    def __init__(self):
        self.checks = {}

    def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        self.checks[name] = check_func

    def run_checks(self) -> Dict[str, Any]:
        results = {}
        for name, func in self.checks.items():
            try:
                results[name] = func()
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results
