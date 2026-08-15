import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class SourceProgress:
    source: str
    status: str = "pending"
    count_found: int = 0
    error: Optional[str] = None


@dataclass
class ScrapeState:
    running: bool = False
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    total_sources: int = 0
    completed: int = 0
    sources: list[SourceProgress] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "running": self.running,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_sources": self.total_sources,
            "completed": self.completed,
            "sources": [asdict(s) for s in self.sources],
        }


class _State:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.state = ScrapeState()

    def begin(self, sources: list[str]) -> None:
        with self._lock:
            self.state = ScrapeState(
                running=True,
                started_at=_now(),
                finished_at=None,
                total_sources=len(sources),
                completed=0,
                sources=[SourceProgress(source=name) for name in sources],
            )

    def start_source(self, source: str) -> None:
        with self._lock:
            for prog in self.state.sources:
                if prog.source == source:
                    prog.status = "running"

    def finish_source(self, source: str, result: dict) -> None:
        with self._lock:
            for prog in self.state.sources:
                if prog.source == source:
                    prog.status = result.get("status", "error")
                    prog.count_found = result.get("count_found", 0)
                    prog.error = result.get("error")
            self.state.completed += 1

    def end(self) -> None:
        with self._lock:
            self.state.running = False
            self.state.finished_at = _now()

    def snapshot(self) -> dict:
        with self._lock:
            return self.state.to_dict()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


state = _State()
