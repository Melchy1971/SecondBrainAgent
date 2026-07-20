import os
from pathlib import Path

import pytest

from secondbrain.desktop_native.lifecycle import InstanceAlreadyRunning, SingleInstanceLock, WindowStateStore


def test_single_instance_rejects_live_owner(tmp_path: Path):
    first = SingleInstanceLock(tmp_path)
    first.acquire()
    try:
        with pytest.raises(InstanceAlreadyRunning):
            SingleInstanceLock(tmp_path).acquire()
    finally:
        first.release()


def test_single_instance_recovers_stale_pid(tmp_path: Path):
    lock = SingleInstanceLock(tmp_path)
    lock.path.parent.mkdir(parents=True)
    lock.path.write_text("999999999", encoding="ascii")
    lock.acquire()
    assert lock.path.read_text(encoding="ascii") == str(os.getpid())
    lock.release()
    assert not lock.path.exists()


def test_window_state_is_atomic_and_validated(tmp_path: Path):
    store = WindowStateStore(tmp_path)
    store.save(geometry="1280x800+20-10", view="Documents")
    assert store.load() == {"geometry": "1280x800+20-10", "view": "Documents"}
    assert not store.path.with_suffix(".tmp").exists()


def test_invalid_or_corrupt_window_state_is_ignored(tmp_path: Path):
    store = WindowStateStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text('{"geometry":"99999x1+0+0","view":"Mail"}', encoding="utf-8")
    assert store.load() == {"view": "Mail"}
    store.path.write_text("not-json", encoding="utf-8")
    assert store.load() == {}
