"""Custom LangGraph checkpointer that writes JSON files to disk."""

import base64
import json
import shutil
import threading
from pathlib import Path
from typing import Any, Optional, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)


def _serde_to_json(serde_tuple: tuple[str, bytes]) -> dict[str, str]:
    """Pack a serde (type, bytes) into a JSON-safe dict."""
    ser_type, blob = serde_tuple
    if ser_type == "json":
        # blob is already JSON text (bytes)
        return {"type": "json", "data": blob.decode("utf-8")}
    # binary formats → base64 so the envelope stays plain JSON
    return {"type": ser_type, "data": base64.b64encode(blob).decode()}


def _json_to_serde(packed: dict[str, str]) -> tuple[str, bytes]:
    """Unpack a JSON dict back into a serde (type, bytes)."""
    ser_type = packed["type"]
    data = packed["data"]
    if ser_type == "json":
        return (ser_type, data.encode("utf-8"))
    return (ser_type, base64.b64decode(data))


def _to_json_serializable(value: Any) -> Any:
    """Coerce non-JSON values (Pydantic models, Enums, etc.) to plain dicts/lists."""
    if isinstance(value, dict):
        return {k: _to_json_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_serializable(v) for v in value]
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _to_json_serializable(value.model_dump())
    return value


class FileSystemSaver(BaseCheckpointSaver):
    """Saves checkpoints as JSON files in a directory.

    File: {checkpoint_dir}/{thread_id}/{checkpoint_id}.json

    Uses LangGraph's built-in ``self.serde`` (typically ``JsonPlusSerializer``)
    so that Pydantic models, tuples, bytes, datetime, etc. survive
    round-trips.  The serde output is stored in a plain-JSON envelope to keep
    the on-disk format inspectable.

    LangGraph dispatches checkpoint writes from a background thread pool, so
    every method that touches disk takes ``self._lock`` to avoid two threads
    writing the same file at once and corrupting it.
    """

    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        super().__init__()

    def _thread_dir(self, thread_id: str) -> Path:
        return self.checkpoint_dir / thread_id

    def _get_latest_path(self, thread_id: str) -> Optional[Path]:
        thread_dir = self._thread_dir(thread_id)
        if not thread_dir.exists():
            return None
        checkpoints = sorted(thread_dir.glob("*.json"))
        return checkpoints[-1] if checkpoints else None

    def _latest_json(self, thread_id: str) -> Optional[dict]:
        """Read and parse the latest checkpoint envelope."""
        path = self._get_latest_path(thread_id)
        if path is None:
            return None
        raw = path.read_text().strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Corrupted file – archive it and treat as missing.
            bad = path.with_suffix(".json.corrupt")
            path.rename(bad)
            return None

    # ------------------------------------------------------------------
    # BaseCheckpointSaver contract
    # ------------------------------------------------------------------

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        with self._lock:
            data = self._latest_json(thread_id)
        if data is None:
            return None

        checkpoint = self.serde.loads_typed(_json_to_serde(data["checkpoint"]))
        metadata = self.serde.loads_typed(_json_to_serde(data["metadata"]))

        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=data.get("parent_config"),
            pending_writes=data.get("pending_writes"),
        )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, Any],
    ) -> RunnableConfig:
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        payload = {
            "config": {"configurable": {"thread_id": thread_id}},
            "checkpoint": _serde_to_json(self.serde.dumps_typed(checkpoint)),
            "metadata": _serde_to_json(self.serde.dumps_typed(metadata)),
        }

        with self._lock:
            thread_dir = self._thread_dir(thread_id)
            thread_dir.mkdir(parents=True, exist_ok=True)

            checkpoint_id = checkpoint.get("id")
            if checkpoint_id is None:
                existing = sorted(thread_dir.glob("*.json"))
                checkpoint_id = str(len(existing))
            path = thread_dir / f"{checkpoint_id}.json"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return config

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        with self._lock:
            data = self._latest_json(thread_id)
            if data is None:
                return

            pending: list = data.get("pending_writes", [])
            # de-dupe by (task_id, channel)
            existing = {(w[0], w[1]) for w in pending if len(w) >= 2}
            for channel, value in writes:
                key = (task_id, channel)
                if key in existing:
                    continue
                pending.append([task_id, channel, _to_json_serializable(value)])

            data["pending_writes"] = pending
            path = self._get_latest_path(thread_id)
            if path:
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list(
        self,
        config: RunnableConfig,
        *,
        limit: Optional[int] = None,
        before: Optional[RunnableConfig] = None,
    ):
        thread_id = config.get("configurable", {}).get("thread_id", "default")

        with self._lock:
            thread_dir = self._thread_dir(thread_id)
            if not thread_dir.exists():
                return

            checkpoints = sorted(thread_dir.glob("*.json"))
            if limit:
                checkpoints = checkpoints[-limit:]

            envelopes = []
            for cp_path in checkpoints:
                raw = cp_path.read_text().strip()
                if not raw:
                    continue
                try:
                    envelopes.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue

        for envelope in envelopes:
            checkpoint = self.serde.loads_typed(_json_to_serde(envelope["checkpoint"]))
            metadata = self.serde.loads_typed(_json_to_serde(envelope["metadata"]))
            yield CheckpointTuple(
                config=RunnableConfig(configurable={"thread_id": thread_id}),
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=envelope.get("parent_config"),
                pending_writes=envelope.get("pending_writes"),
            )

    # ------------------------------------------------------------------
    # Other required overrides
    # ------------------------------------------------------------------

    def delete_thread(self, thread_id: str) -> None:
        thread_dir = self._thread_dir(thread_id)
        if thread_dir.exists():
            shutil.rmtree(thread_dir)

    def delete_for_runs(self, run_ids: Sequence[str]) -> None:
        pass

    def copy_thread(
        self, source_thread_id: str, target_thread_id: str
    ) -> None:
        src = self._thread_dir(source_thread_id)
        dst = self._thread_dir(target_thread_id)
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)

    def prune(
        self, thread_ids: Sequence[str], *, strategy: str = "keep_latest"
    ) -> None:
        for tid in thread_ids:
            thread_dir = self._thread_dir(tid)
            if not thread_dir.exists():
                continue
            if strategy == "delete":
                shutil.rmtree(thread_dir)
            elif strategy == "keep_latest":
                checkpoints = sorted(thread_dir.glob("*.json"))
                if len(checkpoints) > 1:
                    for cp in checkpoints[:-1]:
                        cp.unlink()
