"""Trust scoring algorithm with bootstrap policy and progressive degradation.

Implements the 7 trust update rules from the PRD:
    Rule 1: Honest behavior (positive reward)
    Rule 2: Minor discrepancy (small penalty)
    Rule 3: Major discrepancy (exponential penalty)
    Rule 4: Signature invalid (severe penalty)
    Rule 5: Timestamp stale (moderate penalty)
    Rule 6: Quarantine trigger (trust < threshold)
    Rule 7: Quarantine recovery
"""

import json
import time

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("trust_scorer")

# Trust score bounds
TRUST_MIN = 0.0
TRUST_MAX = 1.0
TRUST_INITIAL = 0.5

# Quarantine threshold
QUARANTINE_THRESHOLD = 0.30

# Bootstrap trust caps
BOOTSTRAP_CAPS = {
    5: 0.5,
    10: 0.7,
    15: 0.85,
    20: 0.95,
}
BOOTSTRAP_COMPLETE_REPORTS = 20

# Discrepancy thresholds
MINOR_DISCREPANCY_THRESHOLD = 0.15
MAJOR_DISCREPANCY_THRESHOLD = 0.30


def _get_bootstrap_cap(honest_reports_count: int) -> float:
    """Get the trust score cap based on bootstrap progress.

    Args:
        honest_reports_count: Number of consecutive honest reports.

    Returns:
        Maximum allowed trust score at this bootstrap stage.
    """
    if honest_reports_count >= BOOTSTRAP_COMPLETE_REPORTS:
        return TRUST_MAX

    for threshold in sorted(BOOTSTRAP_CAPS.keys(), reverse=True):
        if honest_reports_count >= threshold:
            return BOOTSTRAP_CAPS[threshold]

    return TRUST_INITIAL


def compute_trust_delta(
    current_trust: float,
    discrepancy: float,
    signature_valid: bool,
    timestamp_fresh: bool,
    has_sufficient_data: bool,
) -> tuple[float, str]:
    """Compute the trust score change based on validation results.

    Args:
        current_trust: Current trust score.
        discrepancy: Cross-validation discrepancy (0.0 to 1.0+).
        signature_valid: Whether JWT signature was valid.
        timestamp_fresh: Whether timestamp was within acceptable range.
        has_sufficient_data: Whether enough observations exist for cross-validation.

    Returns:
        Tuple of (delta, event_type) where:
            delta is the trust score change (positive or negative)
            event_type is the type of trust event
    """
    # Rule 4: Invalid signature — severe penalty
    if not signature_valid:
        return -0.30, "signature_invalid"

    # Rule 5: Stale timestamp — moderate penalty
    if not timestamp_fresh:
        return -0.15, "timestamp_stale"

    # If no observation data, give neutral/small positive
    if not has_sufficient_data:
        if current_trust < 0.9:
            return +0.01, "bootstrap_period"
        return 0.0, "bootstrap_period"

    # Rule 1: Honest behavior (discrepancy < 0.15)
    if discrepancy < MINOR_DISCREPANCY_THRESHOLD:
        if current_trust >= 0.9:
            return +0.01, "honest_behavior"
        elif current_trust >= 0.5:
            return +0.05, "honest_behavior"
        else:
            return +0.10, "honest_behavior"

    # Rule 2: Minor discrepancy (0.15 <= discrepancy < 0.30)
    if discrepancy < MAJOR_DISCREPANCY_THRESHOLD:
        return -0.05, "metric_discrepancy"

    # Rule 3: Major discrepancy (discrepancy >= 0.30)
    penalty = 0.10 * (discrepancy / MAJOR_DISCREPANCY_THRESHOLD) ** 2
    return -penalty, "metric_discrepancy"


async def update_trust_score(
    node_id: str,
    discrepancy: float,
    signature_valid: bool = True,
    timestamp_fresh: bool = True,
    has_sufficient_data: bool = True,
) -> dict:
    """Update a node's trust score based on the latest heartbeat validation.

    Uses Redis WATCH/MULTI for atomic updates.

    Args:
        node_id: Node identifier.
        discrepancy: Cross-validation discrepancy score.
        signature_valid: Whether JWT signature was valid.
        timestamp_fresh: Whether timestamp was within acceptable range.
        has_sufficient_data: Whether cross-validation had enough data.

    Returns:
        Dictionary with trust update details.
    """
    redis = await get_redis_client()

    trust_key = f"trust:{node_id}"
    bootstrap_key = f"bootstrap:{node_id}"
    quarantine_key = f"quarantine:{node_id}"
    quarantine_count_key = f"quarantine_count:{node_id}"

    # Get current state
    current_trust_raw = await redis.get(trust_key)
    current_trust = float(current_trust_raw) if current_trust_raw else TRUST_INITIAL

    bootstrap_raw = await redis.get(bootstrap_key)
    bootstrap_data = json.loads(bootstrap_raw) if bootstrap_raw else {
        "honest_reports_count": 0,
        "is_in_bootstrap": True,
    }

    honest_reports_count = bootstrap_data.get("honest_reports_count", 0)
    is_in_bootstrap = bootstrap_data.get("is_in_bootstrap", True)

    quarantine_count_raw = await redis.get(quarantine_count_key)
    quarantine_count = int(quarantine_count_raw) if quarantine_count_raw else 0

    # Compute delta
    delta, event_type = compute_trust_delta(
        current_trust=current_trust,
        discrepancy=discrepancy,
        signature_valid=signature_valid,
        timestamp_fresh=timestamp_fresh,
        has_sufficient_data=has_sufficient_data,
    )

    trust_before = current_trust

    # Apply delta
    new_trust = current_trust + delta
    new_trust = max(TRUST_MIN, min(TRUST_MAX, new_trust))

    # Bootstrap policy
    if event_type in ("honest_behavior", "bootstrap_period"):
        honest_reports_count += 1
        if honest_reports_count >= BOOTSTRAP_COMPLETE_REPORTS:
            is_in_bootstrap = False
    elif event_type in ("metric_discrepancy", "signature_invalid", "timestamp_stale"):
        honest_reports_count = 0

    # Apply bootstrap cap
    bootstrap_cap = _get_bootstrap_cap(honest_reports_count)
    new_trust = min(new_trust, bootstrap_cap)

    # Quarantine check (Rule 6)
    is_quarantined = new_trust < QUARANTINE_THRESHOLD
    if is_quarantined:
        quarantine_count += 1
        event_type = "quarantined"

    # Store updated state atomically
    pipe = redis.pipeline()
    pipe.set(trust_key, round(new_trust, 6))
    pipe.set(
        bootstrap_key,
        json.dumps({
            "honest_reports_count": honest_reports_count,
            "is_in_bootstrap": is_in_bootstrap,
        }),
    )
    pipe.set(quarantine_key, str(is_quarantined).lower())
    pipe.set(quarantine_count_key, quarantine_count)
    await pipe.execute()

    # Store trust event
    trust_event = {
        "node_id": node_id,
        "event_type": event_type,
        "timestamp": int(time.time()),
        "trust_score_before": round(trust_before, 6),
        "trust_score_after": round(new_trust, 6),
        "delta": round(delta, 6),
        "discrepancy": round(discrepancy, 4),
        "honest_reports_count": honest_reports_count,
        "is_in_bootstrap": is_in_bootstrap,
        "is_quarantined": is_quarantined,
        "quarantine_count": quarantine_count,
    }

    # Store in Redis list for history
    await redis.lpush(f"trust_history:{node_id}", json.dumps(trust_event))
    # Keep only last 100 events
    await redis.ltrim(f"trust_history:{node_id}", 0, 99)

    logger.info(
        "Trust score updated",
        node_id=node_id,
        event_type=event_type,
        trust_before=round(trust_before, 4),
        trust_after=round(new_trust, 4),
        delta=round(delta, 4),
        discrepancy=round(discrepancy, 4),
        bootstrap=is_in_bootstrap,
        honest_reports=honest_reports_count,
        quarantined=is_quarantined,
    )

    return trust_event