from langchain_core.runnables import RunnableConfig

from nasa_dod_agent.checkpointer import FileSystemSaver


def test_save_and_load_checkpoint(temp_project):
    saver = FileSystemSaver(str(temp_project / ".nasa-dod-agent" / "checkpoints"))
    config = RunnableConfig(configurable={"thread_id": "test-thread"})
    checkpoint = {"ts": "2026-01-01T00:00:00Z", "channel_values": {"x": 1}}
    metadata = {"step": 1}

    saver.put(config, checkpoint, metadata, {})
    loaded = saver.get_tuple(config)
    assert loaded is not None
    assert loaded.checkpoint["ts"] == "2026-01-01T00:00:00Z"

def test_latest_checkpoint(temp_project):
    saver = FileSystemSaver(str(temp_project / ".nasa-dod-agent" / "checkpoints"))
    config = RunnableConfig(configurable={"thread_id": "latest-thread"})

    saver.put(config, {"ts": "1", "channel_values": {}}, {"step": 0}, {})
    saver.put(config, {"ts": "2", "channel_values": {}}, {"step": 1}, {})

    latest = saver.get_tuple(config)
    assert latest is not None
    assert latest.checkpoint["ts"] == "2"

def test_list_checkpoints(temp_project):
    saver = FileSystemSaver(str(temp_project / ".nasa-dod-agent" / "checkpoints"))
    config = RunnableConfig(configurable={"thread_id": "list-thread"})

    saver.put(config, {"ts": "1", "channel_values": {}}, {"step": 0}, {})
    saver.put(config, {"ts": "2", "channel_values": {}}, {"step": 1}, {})

    checkpoints = list(saver.list(config))
    assert len(checkpoints) == 2
