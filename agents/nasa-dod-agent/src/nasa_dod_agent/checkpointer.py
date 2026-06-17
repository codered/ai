"""Custom LangGraph checkpointer that writes JSON files to disk."""

import json
from pathlib import Path
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)


class FileSystemSaver(BaseCheckpointSaver):
    """Saves checkpoints as JSON files in a directory.

    File: {checkpoint_dir}/{thread_id}/{checkpoint_id}.json
    """

    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        super().__init__()

    def _thread_dir(self, thread_id: str) -> Path:
        return self.checkpoint_dir / thread_id

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        thread_dir = self._thread_dir(thread_id)
        if not thread_dir.exists():
            return None

        checkpoints = sorted(thread_dir.glob("*.json"))
        if not checkpoints:
            return None

        latest = checkpoints[-1]
        data = json.loads(latest.read_text())
        return CheckpointTuple(
            config=config,
            checkpoint=data["checkpoint"],
            metadata=data["metadata"],
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
        thread_dir = self._thread_dir(thread_id)
        thread_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_id = checkpoint.get("id")
        if checkpoint_id is None:
            # auto-increment id based on existing files
            existing = sorted(thread_dir.glob("*.json"))
            checkpoint_id = str(len(existing))
        path = thread_dir / f"{checkpoint_id}.json"

        payload = {
            "config": {"configurable": {"thread_id": thread_id}},
            "checkpoint": checkpoint,
            "metadata": metadata,
        }
        path.write_text(json.dumps(payload, indent=2))
        return config

    def list(self, config: RunnableConfig, *, limit: Optional[int] = None, before: Optional[RunnableConfig] = None):
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        thread_dir = self._thread_dir(thread_id)
        if not thread_dir.exists():
            return

        checkpoints = sorted(thread_dir.glob("*.json"))
        if limit:
            checkpoints = checkpoints[-limit:]

        for cp_path in checkpoints:
            data = json.loads(cp_path.read_text())
            yield CheckpointTuple(
                config=RunnableConfig(configurable={"thread_id": thread_id}),
                checkpoint=data["checkpoint"],
                metadata=data["metadata"],
                parent_config=data.get("parent_config"),
                pending_writes=data.get("pending_writes"),
            )
