import pytest

from framcore.events import events


class DummyHandler:
    def __init__(self):  # noqa: ANN204, D107
        self.calls = []

    def handle_event(self, sender, event_type, **kwargs):  # noqa: ANN003
        self.calls.append((sender, event_type, kwargs))


def teardown_function(function):
    # Reset the event handler after each test
    events.set_event_handler(None)


def test_set_and_get_event_handler():
    handler = DummyHandler()
    events.set_event_handler(handler)
    assert events.get_event_handler() is handler

    events.set_event_handler(None)
    assert events.get_event_handler() is None


def test_set_event_handler_invalid():
    class InvalidHandler:
        pass

    with pytest.raises(ValueError):  # noqa: PT011
        events.set_event_handler(InvalidHandler())


def test_send_event_with_handler(capsys):
    handler = DummyHandler()
    events.set_event_handler(handler)
    sender = object()
    events.send_event(sender, "custom_event", foo=123, bar="baz")
    assert handler.calls == [(sender, "custom_event", {"foo": 123, "bar": "baz"})]


def test_send_event_without_handler_prints(capsys):
    events.set_event_handler(None)
    sender = object()
    events.send_event(sender, "custom_event", foo=123)
    captured = capsys.readouterr()
    assert "custom_event" in captured.out
    assert "'foo': 123" in captured.out


@pytest.mark.parametrize(
    ("func", "event_type"),
    [
        (events.send_warning_event, "warning"),
        (events.send_info_event, "info"),
        (events.send_debug_event, "debug"),
    ],
)
def test_send_non_error_events(func, event_type):
    handler = DummyHandler()
    events.set_event_handler(handler)
    func(object(), "test message")
    call = handler.calls[0]
    assert call[1] == event_type
    assert call[2]["message"] == "test message"


def test_send_error_event():
    handler = DummyHandler()
    events.set_event_handler(handler)
    sender = object()
    events.send_error_event(sender, "error occurred", "ValueError", "traceback info")
    call = handler.calls[0]
    assert call[1] == "error"
    assert call[2]["message"] == "error occurred"
    assert call[2]["exception_type_name"] == "ValueError"
    assert call[2]["traceback"] == "traceback info"
