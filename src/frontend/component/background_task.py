"""background_task.py — Thread-safe background task runner for Flet.
Uses page.run_thread() for background work; page.update() is thread-safe in Flet.
"""
from typing import Callable, Any
from share.util.logger_util import LoggerUtil


def run_background_task(
        page,
        vm,
        task_fn: Callable[[], Any],
        finish_fn: Callable[[bool], None],
) -> None:
    """Run task_fn in a background thread, then call finish_fn (still in the thread).

    In Flet 0.86, page.update() is thread-safe, so finish_fn can update the UI
    directly after the task without needing any thread-switching mechanism.

    Args:
        page:      The flet Page instance (used for page.run_thread & page.update).
        vm:        ViewModel with an `is_loading` bool property.
        task_fn:   Callable that performs the work; returns truthy on success.
        finish_fn: Callable(success: bool) called after task (still in background thread).
    """
    # Prevent double start
    if getattr(vm, 'is_loading', False):
        return

    vm.is_loading = True
    try:
        page.update()
    except Exception:
        pass

    def _worker():
        result = False
        try:
            result = bool(task_fn())
        except Exception as e:
            LoggerUtil.get_logger().exception(
                f"run_background_task: exception in task: {e}")
            result = False
        finally:
            try:
                finish_fn(result)
            except Exception as e:
                LoggerUtil.get_logger().exception(
                    f"run_background_task: exception in finish_fn: {e}")
            try:
                vm.is_loading = False
                page.update()
            except Exception:
                pass

    page.run_thread(_worker)
