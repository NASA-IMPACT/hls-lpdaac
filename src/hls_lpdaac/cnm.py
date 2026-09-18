from __future__ import annotations

from typing import Any


class ProviderAlreadySetError(ValueError):
    """Raised when a CNM manifest read from S3 already carries a provider."""


def add_provider(manifest: dict[str, Any], provider: str) -> dict[str, Any]:
    """Return a copy of manifest carrying the given CNM provider.

    The provider identifies the LPDAAC queue the message is bound for, so only
    the forwarder can set it. A manifest that arrives with one already set
    breaks that invariant and is rejected rather than overwritten, so the
    message reaches the dead-letter queue with its original content intact.

    Raises ProviderAlreadySetError if manifest already has a provider.
    """
    if "provider" in manifest:
        raise ProviderAlreadySetError(
            f"manifest already has provider {manifest['provider']!r}"
        )

    return {**manifest, "provider": provider}
