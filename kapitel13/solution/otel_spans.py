"""Spans nach den OpenTelemetry GenAI Semantic Conventions.
Status der Konventionen: Development. Alle Attributnamen
stehen in ATTR und nirgends sonst."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode

ATTR = {  # Kurzname im Code -> Name in der Konvention
    "op": "gen_ai.operation.name",
    "provider": "gen_ai.provider.name",
    "model": "gen_ai.request.model",
    "workflow": "gen_ai.workflow.name",
    "agent": "gen_ai.agent.name",
    "tool": "gen_ai.tool.name",
    "tokens_in": "gen_ai.usage.input_tokens",
    "tokens_out": "gen_ai.usage.output_tokens",
    "error": "error.type",
}
_tracer = trace.get_tracer("agentic-werkstatt")


def setup(exporter) -> None:
    """Einmal pro Prozess: wohin die Spans gehen."""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def gen_ai_span(op: str, name: str, **attrs):
    """Span mit dem Namen '{op} {name}', z. B. 'chat
    llama3.2-16k' oder 'execute_tool read_file'."""
    a = {ATTR["op"]: op}
    a |= {ATTR[k]: v for k, v in attrs.items()}
    return _tracer.start_as_current_span(f"{op} {name}",
                                         attributes=a)


def set_attrs(span, **attrs) -> None:
    for k, v in attrs.items():
        span.set_attribute(ATTR[k], v)


def mark_error(span, kind: str, message: str) -> None:
    span.set_status(Status(StatusCode.ERROR, message[:120]))
    span.set_attribute(ATTR["error"], kind)
