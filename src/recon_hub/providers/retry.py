import asyncio
from typing import Any, Awaitable, Callable


async def with_retry(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    retries: int = 3,
    base_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - network error path
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("with_retry failed without exception")
