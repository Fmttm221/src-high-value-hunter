import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                host TEXT,
                ip TEXT,
                port INTEGER,
                url TEXT,
                source TEXT,
                tags TEXT,
                priority INTEGER DEFAULT 0,
                alive INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                endpoint TEXT,
                param TEXT,
                role TEXT,
                auth_state TEXT,
                standalone_impact TEXT,
                chain_roles TEXT,
                monetization_paths TEXT,
                submission TEXT,
                evidence_refs TEXT,
                reproducible INTEGER DEFAULT 0,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS endpoints (
                id TEXT PRIMARY KEY,
                url TEXT,
                method TEXT,
                params TEXT,
                auth_state TEXT,
                role TEXT,
                data_sensitivity TEXT,
                monetization_tags TEXT,
                priority INTEGER DEFAULT 0,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS chains (
                id TEXT PRIMARY KEY,
                nodes TEXT,
                edges TEXT,
                target_monetization TEXT,
                status TEXT,
                evidence_refs TEXT,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS throttle_profiles (
                host TEXT PRIMARY KEY,
                waf TEXT,
                mode TEXT,
                safe_concurrency INTEGER,
                safe_rps REAL,
                delay_ms INTEGER,
                backoff_on TEXT,
                cooldown_seconds INTEGER,
                ip_blocked INTEGER,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                role TEXT,
                tenant TEXT,
                cookies TEXT,
                jwt TEXT,
                tokens TEXT,
                csrf TEXT,
                valid INTEGER,
                expires_at TEXT,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                role TEXT,
                tenant TEXT,
                phone TEXT,
                email TEXT,
                password TEXT,
                state TEXT,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                source TEXT,
                type TEXT,
                status TEXT,
                progress REAL,
                payload TEXT,
                external_ref TEXT,
                result TEXT,
                error TEXT,
                host TEXT,
                provider TEXT,
                created_at TEXT,
                updated_at TEXT,
                started_at TEXT,
                finished_at TEXT,
                extra TEXT
            );

            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS provider_cache (
                cache_key TEXT PRIMARY KEY,
                provider TEXT,
                query TEXT,
                response TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS evidence_index (
                id TEXT PRIMARY KEY,
                finding_id TEXT,
                path TEXT,
                sha256 TEXT,
                redacted INTEGER,
                created_at TEXT,
                extra TEXT
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def set_state(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO state(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self.conn.commit()

    def get_state(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute(
            "SELECT value FROM state WHERE key=?", (key,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def save_throttle(self, profile: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO throttle_profiles(
                host, waf, mode, safe_concurrency, safe_rps, delay_ms,
                backoff_on, cooldown_seconds, ip_blocked, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(host) DO UPDATE SET
                waf=excluded.waf,
                mode=excluded.mode,
                safe_concurrency=excluded.safe_concurrency,
                safe_rps=excluded.safe_rps,
                delay_ms=excluded.delay_ms,
                backoff_on=excluded.backoff_on,
                cooldown_seconds=excluded.cooldown_seconds,
                ip_blocked=excluded.ip_blocked,
                extra=excluded.extra
            """,
            (
                profile.get("host", ""),
                json.dumps(profile.get("waf", {}), ensure_ascii=False),
                profile.get("mode", "conservative"),
                profile.get("safe_concurrency", 1),
                profile.get("safe_rps", 1.0),
                profile.get("delay_ms", 500),
                json.dumps(profile.get("backoff_on", [403, 429, 503]), ensure_ascii=False),
                profile.get("cooldown_seconds", 300),
                1 if profile.get("ip_blocked") else 0,
                json.dumps(profile.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def get_throttle(self, host: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM throttle_profiles WHERE host=?", (host,)
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["waf"] = json.loads(data.get("waf") or "{}")
        data["backoff_on"] = json.loads(data.get("backoff_on") or "[]")
        data["extra"] = json.loads(data.get("extra") or "{}")
        data["ip_blocked"] = bool(data.get("ip_blocked"))
        return data

    def save_task(self, task: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO tasks(
                id, source, type, status, progress, payload, external_ref,
                result, error, host, provider, created_at, updated_at,
                started_at, finished_at, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                progress=excluded.progress,
                result=excluded.result,
                error=excluded.error,
                updated_at=excluded.updated_at,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                extra=excluded.extra
            """,
            (
                task.get("id"),
                task.get("source", "recon-hub"),
                task.get("type", ""),
                task.get("status", "queued"),
                task.get("progress", 0.0),
                json.dumps(task.get("payload", {}), ensure_ascii=False),
                task.get("external_ref", ""),
                json.dumps(task.get("result", {}), ensure_ascii=False),
                task.get("error", ""),
                task.get("host", ""),
                task.get("provider", ""),
                task.get("created_at", ""),
                task.get("updated_at", ""),
                task.get("started_at", ""),
                task.get("finished_at", ""),
                json.dumps(task.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_asset(self, asset: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO assets(
                id, type, host, ip, port, url, source, tags, priority,
                alive, first_seen, last_seen, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                host=excluded.host,
                ip=excluded.ip,
                port=excluded.port,
                url=excluded.url,
                source=excluded.source,
                tags=excluded.tags,
                priority=excluded.priority,
                alive=excluded.alive,
                last_seen=excluded.last_seen,
                extra=excluded.extra
            """,
            (
                asset.get("id"),
                asset.get("type", ""),
                asset.get("host", ""),
                asset.get("ip", ""),
                asset.get("port"),
                asset.get("url", ""),
                asset.get("source", ""),
                json.dumps(asset.get("tags", []), ensure_ascii=False),
                asset.get("priority", 0),
                1 if asset.get("alive") else 0,
                asset.get("first_seen", ""),
                asset.get("last_seen", ""),
                json.dumps(asset.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_assets(self, assets: list[dict[str, Any]]) -> int:
        for asset in assets:
            self.save_asset(asset)
        return len(assets)

    def list_assets(
        self,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
        host_like: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM assets"
        params: list[Any] = []
        where: list[str] = []

        if type:
            where.append("type = ?")
            params.append(type)
        if host_like:
            where.append("host LIKE ?")
            params.append(f"%{host_like}%")

        if where:
            query += " WHERE " + " AND ".join(where)

        query += " ORDER BY priority DESC, last_seen DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(query, params).fetchall()
        assets: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            for key in ("tags", "extra"):
                raw = data.get(key)
                if isinstance(raw, str) and raw:
                    try:
                        data[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
            data["alive"] = bool(data.get("alive"))
            assets.append(data)
        return assets

    def save_endpoint(self, endpoint: dict[str, Any]) -> None:
        endpoint_id = endpoint.get("id")
        if not endpoint_id:
            key = f"{endpoint.get('method', 'GET')}:{endpoint.get('url', '')}"
            endpoint_id = hashlib.sha256(key.encode("utf-8")).hexdigest()

        self.conn.execute(
            """
            INSERT INTO endpoints(
                id, url, method, params, auth_state, role,
                data_sensitivity, monetization_tags, priority, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                url=excluded.url,
                method=excluded.method,
                params=excluded.params,
                auth_state=excluded.auth_state,
                role=excluded.role,
                data_sensitivity=excluded.data_sensitivity,
                monetization_tags=excluded.monetization_tags,
                priority=excluded.priority,
                extra=excluded.extra
            """,
            (
                endpoint_id,
                endpoint.get("url", ""),
                endpoint.get("method", "GET"),
                json.dumps(endpoint.get("params", []), ensure_ascii=False),
                endpoint.get("auth_state", "anonymous"),
                endpoint.get("role", ""),
                endpoint.get("data_sensitivity", ""),
                json.dumps(endpoint.get("monetization_tags", []), ensure_ascii=False),
                endpoint.get("priority", 0),
                json.dumps(endpoint.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_endpoints(self, endpoints: list[dict[str, Any]]) -> int:
        for endpoint in endpoints:
            self.save_endpoint(endpoint)
        return len(endpoints)

    def list_endpoints(
        self,
        limit: int = 100,
        offset: int = 0,
        url_like: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM endpoints"
        params: list[Any] = []
        if url_like:
            query += " WHERE url LIKE ?"
            params.append(f"%{url_like}%")
        query += " ORDER BY priority DESC, rowid DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        endpoints: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            for key in ("params", "monetization_tags", "extra"):
                raw = data.get(key)
                if isinstance(raw, str) and raw:
                    try:
                        data[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
            endpoints.append(data)
        return endpoints

    def save_finding(self, finding: dict[str, Any]) -> None:
        finding_id = finding.get("id")
        if not finding_id:
            key = f"{finding.get('type', '')}:{finding.get('endpoint', '')}:{finding.get('param', '')}"
            finding_id = hashlib.sha256(key.encode("utf-8")).hexdigest()

        self.conn.execute(
            """
            INSERT INTO findings(
                id, type, endpoint, param, role, auth_state,
                standalone_impact, chain_roles, monetization_paths,
                submission, evidence_refs, reproducible, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type=excluded.type,
                endpoint=excluded.endpoint,
                param=excluded.param,
                role=excluded.role,
                auth_state=excluded.auth_state,
                standalone_impact=excluded.standalone_impact,
                chain_roles=excluded.chain_roles,
                monetization_paths=excluded.monetization_paths,
                submission=excluded.submission,
                evidence_refs=excluded.evidence_refs,
                reproducible=excluded.reproducible,
                extra=excluded.extra
            """,
            (
                finding_id,
                finding.get("type", ""),
                finding.get("endpoint", ""),
                finding.get("param", ""),
                finding.get("role", ""),
                finding.get("auth_state", ""),
                finding.get("standalone_impact", ""),
                json.dumps(finding.get("chain_roles", []), ensure_ascii=False),
                json.dumps(finding.get("monetization_paths", []), ensure_ascii=False),
                finding.get("submission", "discard"),
                json.dumps(finding.get("evidence_refs", []), ensure_ascii=False),
                1 if finding.get("reproducible") else 0,
                json.dumps(finding.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_findings(self, findings: list[dict[str, Any]]) -> int:
        for finding in findings:
            self.save_finding(finding)
        return len(findings)

    def list_findings(
        self,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM findings"
        params: list[Any] = []
        if type:
            query += " WHERE type = ?"
            params.append(type)
        query += " ORDER BY rowid DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        findings: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            for key in ("chain_roles", "monetization_paths", "evidence_refs", "extra"):
                raw = data.get(key)
                if isinstance(raw, str) and raw:
                    try:
                        data[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
            data["reproducible"] = bool(data.get("reproducible"))
            findings.append(data)
        return findings

    def save_chain(self, chain: dict[str, Any]) -> None:
        chain_id = chain.get("id")
        if not chain_id:
            key = json.dumps(
                {"nodes": chain.get("nodes", []), "edges": chain.get("edges", [])},
                sort_keys=True,
                ensure_ascii=False,
            )
            chain_id = hashlib.sha256(key.encode("utf-8")).hexdigest()

        self.conn.execute(
            """
            INSERT INTO chains(
                id, nodes, edges, target_monetization, status, evidence_refs, extra
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nodes=excluded.nodes,
                edges=excluded.edges,
                target_monetization=excluded.target_monetization,
                status=excluded.status,
                evidence_refs=excluded.evidence_refs,
                extra=excluded.extra
            """,
            (
                chain_id,
                json.dumps(chain.get("nodes", []), ensure_ascii=False),
                json.dumps(chain.get("edges", []), ensure_ascii=False),
                chain.get("target_monetization", ""),
                chain.get("status", "incomplete"),
                json.dumps(chain.get("evidence_refs", []), ensure_ascii=False),
                json.dumps(chain.get("extra", {}), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def save_chains(self, chains: list[dict[str, Any]]) -> int:
        for chain in chains:
            self.save_chain(chain)
        return len(chains)

    def list_chains(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM chains ORDER BY rowid DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        chains: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            for key in ("nodes", "edges", "evidence_refs", "extra"):
                raw = data.get(key)
                if isinstance(raw, str) and raw:
                    try:
                        data[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
            chains.append(data)
        return chains

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        for key in ("payload", "result", "extra"):
            raw = data.get(key)
            if isinstance(raw, str) and raw:
                try:
                    data[key] = json.loads(raw)
                except json.JSONDecodeError:
                    pass
        return data
