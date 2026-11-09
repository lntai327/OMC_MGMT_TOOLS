"""Base ViewModel — lightweight observer pattern replacing pypubsub."""
from collections import defaultdict
from typing import Callable


class BaseViewModel:
    """Observable base for all ViewModels.

    Usage:
        vm.subscribe("is_loading", lambda: update_ui())
        vm.notify("is_loading")
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, key: str, callback: Callable) -> None:
        """Register a callback for a property key."""
        if callback not in self._subscribers[key]:
            self._subscribers[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable) -> None:
        """Remove a previously registered callback."""
        try:
            self._subscribers[key].remove(callback)
        except ValueError:
            pass

    def notify(self, key: str) -> None:
        """Notify all subscribers for the given property key."""
        for cb in list(self._subscribers.get(key, [])):
            try:
                cb()
            except Exception as e:
                from share.util.logger_util import LoggerUtil
                LoggerUtil.get_logger().error(f"BaseViewModel notify '{key}' callback error: {e}")
