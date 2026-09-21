from typing import Any

from constructs import Construct

from .notification import ConstructIds, NotificationStack as BaseNotificationStack

HANDLER = "hls_lpdaac.historical.index.handler"
QUEUE_URL_VARIABLE = "QUEUE_URL"

# Fixed: these ids determine the deployed logical ids.
IDS = ConstructIds(
    bucket="HistoricalBucket",
    lpdaac_queue="HistoricalQueue",
    dead_letter_queue="HistoricalNotificationDLQ",
    notification_queue="HistoricalNotificationQueue",
    function="HistoricalLambda",
)


class NotificationStack(BaseNotificationStack):
    def __init__(
        self,
        scope: Construct,
        stack_name: str,
        *,
        bucket_name: str,
        queue_arn: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            scope,
            stack_name,
            bucket_name=bucket_name,
            queue_arn=queue_arn,
            ids=IDS,
            handler=HANDLER,
            queue_url_variable=QUEUE_URL_VARIABLE,
            **kwargs,
        )

    # Retained for the integration test app, which reads these names.
    @property
    def lpdaac_historical_bucket(self):
        return self.bucket

    @property
    def lpdaac_historical_queue(self):
        return self.lpdaac_queue

    @property
    def lpdaac_historical_lambda(self):
        return self.notification_function
