from typing import Any

from constructs import Construct

from .notification import ConstructIds, NotificationStack as BaseNotificationStack

HANDLER = "hls_lpdaac.forward.index.handler"
QUEUE_URL_VARIABLE = "LPDAAC_QUEUE_URL"

# Fixed: these ids determine the deployed logical ids.
IDS = ConstructIds(
    bucket="hls-output",
    lpdaac_queue="lpdaac",
    dead_letter_queue="NotificationDLQ",
    notification_queue="NotificationQueue",
    function="ForwardNotifier",
)


class NotificationStack(BaseNotificationStack):
    def __init__(
        self,
        scope: Construct,
        stack_name: str,
        *,
        bucket_name: str,
        lpdaac_queue_arn: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            scope,
            stack_name,
            bucket_name=bucket_name,
            queue_arn=lpdaac_queue_arn,
            ids=IDS,
            handler=HANDLER,
            queue_url_variable=QUEUE_URL_VARIABLE,
            **kwargs,
        )
