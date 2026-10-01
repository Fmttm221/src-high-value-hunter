import uuid
from typing import Any


def register_task_tools(mcp, storage, config):
    @mcp.tool()
    def recon_task_start(
        type: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start a light recon-hub task."""
        task_id = str(uuid.uuid4())
        storage.save_task(
            {
                "id": task_id,
                "type": type,
                "status": "queued",
                "payload": payload or {},
            }
        )
        return {"task_id": task_id, "status": "queued"}

    @mcp.tool()
    def recon_task_register(
        type: str,
        payload: dict[str, Any] | None = None,
        external_ref: str = "",
        host: str = "",
        provider: str = "",
    ) -> dict[str, Any]:
        """Register an external task, e.g. a hexstrike job."""
        task_id = str(uuid.uuid4())
        storage.save_task(
            {
                "id": task_id,
                "source": "external",
                "type": type,
                "status": "queued",
                "payload": payload or {},
                "external_ref": external_ref,
                "host": host,
                "provider": provider,
            }
        )
        return {"task_id": task_id, "status": "queued"}

    @mcp.tool()
    def recon_task_update(
        task_id: str,
        status: str | None = None,
        progress: float | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update task state."""
        task = storage.get_task(task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        if status is not None:
            task["status"] = status
        if progress is not None:
            task["progress"] = progress
        if result is not None:
            task["result"] = result
        if error is not None:
            task["error"] = error
        storage.save_task(task)
        return {"task_id": task_id, "status": task["status"]}

    @mcp.tool()
    def recon_task_status(task_id: str) -> dict[str, Any]:
        """Get task status."""
        task = storage.get_task(task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        return task

    @mcp.tool()
    def recon_task_cancel(task_id: str) -> dict[str, Any]:
        """Cancel a task."""
        task = storage.get_task(task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        task["status"] = "cancelled"
        storage.save_task(task)
        return {"task_id": task_id, "status": "cancelled"}

    @mcp.tool()
    def recon_task_result(task_id: str) -> dict[str, Any]:
        """Get task result."""
        task = storage.get_task(task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        return {
            "task_id": task_id,
            "status": task.get("status"),
            "result": task.get("result", {}),
        }
