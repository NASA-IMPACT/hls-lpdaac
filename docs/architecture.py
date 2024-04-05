from diagrams import Cluster, Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SNS, SQS
from diagrams.aws.storage import S3

with Diagram(
    "HLS Notification",
    show=False,
    filename="docs/architecture",
    outformat="png",
):
    hls_bucket = S3("HLS Bucket")

    with Cluster("Forward Notification App"):
        with Cluster("Main Stack"):
            hls_topic = SNS("HLS Topic")

            tiler_notifier = Lambda("Tiler Notifier")
            lpdaac_buffer_queue = SQS("LPDAAC Buffer")

            lpdaac_dlq = lpdaac_buffer_queue >> SQS("DLQ")
            lpdaac_redriver = lpdaac_dlq >> Lambda("Redriver")
            lpdaac_redriver >> lpdaac_buffer_queue  # type: ignore[reportUnusedExpression]

        with Cluster("LPDAAC Maintenance Stack"):
            lpdaac_handler = lpdaac_buffer_queue >> Lambda("LPDAAC Notifier")

    with Cluster("LPDAAC Cumulus"):
        lpdaac_handler >> SQS("LPDAAC Queue")  # type: ignore[reportUnusedExpression]

    with Cluster("Tiler Service"):
        tiler_notifier >> SQS("Tiler Queue")  # type: ignore[reportUnusedExpression]

    hls_bucket >> hls_topic >> [lpdaac_buffer_queue, tiler_notifier]  # type: ignore[reportUnusedExpression]
