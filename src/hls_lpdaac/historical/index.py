from __future__ import annotations

import os
from typing import TYPE_CHECKING

from hls_lpdaac.notify import forward_notifications

if TYPE_CHECKING:  # pragma: no cover
    from aws_lambda_typing.context import Context
    from aws_lambda_typing.events import SQSEvent

# Identifies the LPDAAC queue this stack publishes to. LPDAAC matches provider
# names to their ingest queues, so the value must track the queue ARN this
# stack is deployed against.
PROVIDER = "lp_HLS_2.0_BACKWARD_PROCESSED"


def handler(event: "SQSEvent", _: "Context") -> dict:
    return _handler(  # pragma: no cover
        event,
        queue_url=os.environ["QUEUE_URL"],
    )


# Enables unit testing without the need to monkeypatch `os.environ` (which would
# be necessary to test `handler` above).
def _handler(
    event: "SQSEvent",
    *,
    queue_url: str,
    provider: str = PROVIDER,
) -> dict:
    return forward_notifications(event, queue_url=queue_url, provider=provider)
