import pytest
from opentelemetry.sdk.trace.export import (
    in_memory_span_exporter as mem,
)

from otel_spans import setup

EXPORTER = mem.InMemorySpanExporter()
setup(EXPORTER)              # einmal pro Prozess


@pytest.fixture
def spans():
    EXPORTER.clear()
    yield EXPORTER.get_finished_spans
