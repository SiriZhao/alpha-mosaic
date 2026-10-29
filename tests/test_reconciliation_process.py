"""A genuinely terminated owned parent releases leases without inventing child success."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from alphamosaic.common.locking import ResearchBusyError
from alphamosaic.core.service import ApplicationService
from alphamosaic.experiments.runner import digest


def terminate_owned_parent(process: subprocess.Popen[bytes], actual_pid: int) -> None:
    if actual_pid == process.pid:
        process.terminate()
        return
    # Windows venv python.exe can be a redirector with a separate Python child.
    # Prove native lineage and executable identity before terminating that child.
    assert sys.platform == "win32" and process.poll() is None
    import ctypes
    from ctypes import wintypes
    class BasicInformation(ctypes.Structure):
        pid: int
        parent_pid: int
        _fields_ = [("reserved", ctypes.c_void_p), ("peb", ctypes.c_void_p),
            ("reserved_pair", ctypes.c_void_p * 2), ("pid", ctypes.c_size_t), ("parent_pid", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    query = ctypes.WinDLL("ntdll").NtQueryInformationProcess
    query.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.c_void_p]
    query.restype = ctypes.c_long
    handle = kernel.OpenProcess(0x0400 | 0x1000 | 0x100000 | 0x0001, False, actual_pid)
    assert handle, "cannot query the owned Python parent"
    try:
        basic = BasicInformation()
        assert query(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic), None) == 0
        assert basic.pid == actual_pid and basic.parent_pid == process.pid
        executable = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(executable))
        assert kernel.QueryFullProcessImageNameW(handle, 0, executable, ctypes.byref(size))
        base_executable = getattr(sys, "_base_executable", None)
        assert isinstance(base_executable, str)
        assert Path(executable.value).resolve() == Path(base_executable).resolve()
        assert kernel.TerminateProcess(handle, 1)
        assert kernel.WaitForSingleObject(handle, 10000) == 0
    finally:
        kernel.CloseHandle(handle)


def test_terminated_parent_preserves_sealed_child_artifact_and_reconciles_without_retry(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path)
    dataset = service.research_demo(80)["dataset_id"]
    plan = service.plan_research({"dataset_id": dataset,
        "question": "Does a genuinely terminated research parent preserve a sealed child artifact without retrying its uncertain call?",
        "strategies": ["buy_and_hold"], "cost_scenarios": ["realistic", "stress"],
        "per_experiment_seconds": 30, "total_seconds": 60})
    marker = tmp_path / "owned-parent-ready.json"
    code = """
import json, os, sys
from pathlib import Path
from alphamosaic.core.service import ApplicationService
service = ApplicationService(Path(sys.argv[1]))
workflow = service.research_workflow()
worker = workflow._worker
def pause_before_recording(*args):
    outcome = worker(*args)
    if outcome['status'] != 'COMPLETED':
        raise RuntimeError('fixture child did not complete: ' + str(outcome))
    with Path(sys.argv[3]).open('x', encoding='utf-8') as stream:
        json.dump({'parent_pid': os.getpid(), 'experiment_id': outcome['experiment_id']}, stream)
    sys.stdin.read(1)
    return outcome
workflow._worker = pause_before_recording
service.run_research_plan(sys.argv[2])
"""
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT", "TEMP", "TMP", "LANG", "LC_ALL", "PYTHONUTF8"}}
    source = Path(__file__).resolve().parents[1] / "src"
    environment["PYTHONPATH"] = str(source)
    process = subprocess.Popen([sys.executable, "-W", "error::RuntimeWarning", "-c", code,
        str(tmp_path), plan["plan_id"], str(marker)], cwd=source, env=environment,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    try:
        deadline = time.monotonic() + 45
        ready = None
        while ready is None:
            assert process.poll() is None, "owned parent exited before its ready marker"
            assert time.monotonic() < deadline, "bounded child did not reach the parent handoff"
            try:
                ready = json.loads(marker.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(.02)
        assert isinstance(ready["parent_pid"], int) and process.poll() is None
        with pytest.raises(ResearchBusyError):
            service.reconcile_research_plan(plan["plan_id"])
        directory = tmp_path / "experiments" / ready["experiment_id"]
        original = {p.name: digest(p.read_bytes()) for p in directory.iterdir() if p.is_file()}
        terminate_owned_parent(process, ready["parent_pid"])
        process.wait(timeout=10)
        assert process.returncode != 0
        state = service.reconcile_research_plan(plan["plan_id"])
        record = next(e["payload"] for e in state["events"] if e["kind"] == "RECOVERED_ATTEMPT")
        assert state["status"] == "INTERRUPTED" and record["exit_status"] == "NOT_OBSERVED"
        assert record["classification"] == "RECOVERED_COMPLETED_ARTIFACT"
        assert record["artifact"]["experiment_id"] == ready["experiment_id"]
        assert not any(e["kind"] == "TOOL_RESULT" for e in state["events"])
        assert {p.name: digest(p.read_bytes()) for p in directory.iterdir() if p.is_file()} == original
        assert len(service.research_experiments()) == 1
        assert service.run_research_plan(plan["plan_id"]) == state
        assert service.reconcile_research_plan(plan["plan_id"]) == state
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()
