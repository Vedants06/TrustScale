"""Prometheus metrics for trust engine state."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

trust_score_gauge = Gauge(
    "trustscale_node_trust_score",
    "Current trust score for a node",
    ["node_id"],
)

quarantine_status_gauge = Gauge(
    "trustscale_node_is_quarantined",
    "Whether a node is currently quarantined (1=yes, 0=no)",
    ["node_id"],
)

quarantine_count_gauge = Gauge(
    "trustscale_node_quarantine_count",
    "Total number of times a node has been quarantined",
    ["node_id"],
)

discrepancy_gauge = Gauge(
    "trustscale_node_discrepancy",
    "Latest cross-validation discrepancy for a node",
    ["node_id"],
)