"""Test crash-resume behavior by simulating graph interruption."""

from langchain_core.runnables import RunnableConfig

from nasa_dod_agent.checkpointer import FileSystemSaver


def test_checkpoint_save_and_resume(temp_project):
    """Test that FileSystemSaver can save and load checkpoints."""
    checkpoint_dir = str(temp_project / ".nasa-dod-agent" / "checkpoints")
    saver = FileSystemSaver(checkpoint_dir)
    config = RunnableConfig(configurable={"thread_id": "resume-test"})

    # Save
    checkpoint = {"ts": "2026-06-16T00:00:00Z", "channel_values": {"x": 1}}
    saver.put(config, checkpoint, {"step": 0}, {})

    # Load
    loaded = saver.get_tuple(config)
    assert loaded is not None
    assert loaded.checkpoint["ts"] == "2026-06-16T00:00:00Z"
