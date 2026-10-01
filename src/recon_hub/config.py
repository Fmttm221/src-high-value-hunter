from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml


@dataclass
class ServerConfig:
    name: str = "recon-hub"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class StorageConfig:
    sqlite: str = "./data/recon.db"
    jsonl_dir: str = "./data/jsonl"


@dataclass
class NetworkConfig:
    proxy: str = ""
    clash_api: str = ""
    clash_secret: str = ""
    clash_group: str = ""


@dataclass
class ProviderConfig:
    enabled: bool = True
    api_key: str = ""
    api_id: str = ""
    api_secret: str = ""


@dataclass
class Config:
    server: ServerConfig = field(default_factory=ServerConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    providers: dict[str, ProviderConfig] = field(default_factory=dict)


def _provider_config(data: dict | None) -> dict[str, ProviderConfig]:
    out: dict[str, ProviderConfig] = {}
    for name, cfg in (data or {}).items():
        out[name] = ProviderConfig(
            enabled=bool(cfg.get("enabled", True)),
            api_key=str(cfg.get("api_key", "")),
            api_id=str(cfg.get("api_id", "")),
            api_secret=str(cfg.get("api_secret", "")),
        )
    return out


def load_config(path: str | None = None) -> Config:
    config_path = path or os.environ.get("RECON_HUB_CONFIG", "./config.yaml")
    p = Path(config_path)
    if not p.exists():
        return Config()

    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return Config(
        server=ServerConfig(**raw.get("server", {})),
        storage=StorageConfig(**raw.get("storage", {})),
        network=NetworkConfig(**raw.get("network", {})),
        providers=_provider_config(raw.get("providers")),
    )
