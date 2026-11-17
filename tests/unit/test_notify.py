import pytest

from hls_lpdaac.notify import INJECT_PROVIDER_VARIABLE, inject_provider_from_env


def test_injects_the_provider_when_the_variable_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(INJECT_PROVIDER_VARIABLE, raising=False)

    assert inject_provider_from_env()


@pytest.mark.parametrize(
    "value, expected", [("true", True), ("false", False), ("FALSE", False)]
)
def test_reads_the_inject_provider_variable(
    monkeypatch: pytest.MonkeyPatch, value: str, expected: bool
) -> None:
    monkeypatch.setenv(INJECT_PROVIDER_VARIABLE, value)

    assert inject_provider_from_env() is expected
