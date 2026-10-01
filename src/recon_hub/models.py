from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Asset:
    id: str
    type: str
    host: str = ""
    ip: str = ""
    port: int | None = None
    url: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    priority: int = 0
    alive: bool = False
    first_seen: str = ""
    last_seen: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    id: str
    type: str
    endpoint: str = ""
    param: str = ""
    role: str = ""
    auth_state: str = ""
    standalone_impact: str = ""
    chain_roles: list[str] = field(default_factory=list)
    monetization_paths: list[str] = field(default_factory=list)
    submission: str = "discard"
    evidence_refs: list[str] = field(default_factory=list)
    reproducible: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Chain:
    id: str
    nodes: list[str] = field(default_factory=list)
    edges: list[dict[str, str]] = field(default_factory=list)
    target_monetization: str = ""
    status: str = "incomplete"
    evidence_refs: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Session:
    id: str
    account_id: str = ""
    role: str = ""
    tenant: str = ""
    cookies: dict[str, str] = field(default_factory=dict)
    jwt: str = ""
    tokens: dict[str, str] = field(default_factory=dict)
    csrf: str = ""
    valid: bool = False
    expires_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThrottleProfile:
    host: str
    waf: dict[str, Any] = field(default_factory=dict)
    mode: str = "conservative"
    safe_concurrency: int = 1
    safe_rps: float = 1.0
    delay_ms: int = 500
    backoff_on: list[int] = field(default_factory=lambda: [403, 429, 503])
    cooldown_seconds: int = 300
    ip_blocked: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Task:
    id: str
    source: str = "recon-hub"
    type: str = ""
    status: str = "queued"
    progress: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)
    external_ref: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    host: str = ""
    provider: str = ""
    created_at: str = ""
    updated_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
