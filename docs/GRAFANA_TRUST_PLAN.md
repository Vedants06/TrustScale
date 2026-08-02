# Grafana Trust Dashboard Plan

## Overview

This document outlines the planned Grafana dashboard for visualizing TrustScale node trust behavior. The dashboard will be implemented after Phase 22, when the required trust metrics become available.

---

## Panel 1: Current Trust Score per Node

**Purpose**
- Display the current trust score for each node.
- Quickly identify nodes with low trust.

**Data Source**
- Prometheus Metric: `trustscale_node_trust_score`
- Temporary API (if needed): `GET /nodes/{node_id}/trust`

**Visualization**
- Gauge

**Range**
- 0.0 to 1.0

---

## Panel 2: Trust Score Over Time

**Purpose**
- Visualize how trust changes over time.
- Detect gradual degradation or recovery.

**Data Source**
- `trustscale_node_trust_score`

**Visualization**
- Time Series

---

## Panel 3: Quarantine Events

**Purpose**
- Display how many times each node has been quarantined.
- Help identify unstable or malicious nodes.

**Data Source**
- `trustscale_node_quarantine_count`

**Visualization**
- Bar Chart / Stat Panel

---

## Panel 4: Request Distribution Across Nodes

**Purpose**
- Show how requests are distributed among active nodes.
- Verify load balancing behavior.

**Data Source**
- `trustscale_node_requests_last_30s`

**Visualization**
- Time Series

---

## Panel 5: Discrepancy Values Over Time

**Purpose**
- Visualize cross-validation discrepancy values.
- Detect suspicious node behavior.

**Data Source**
- `trustscale_node_discrepancy`

**Visualization**
- Time Series

---

## Future Metrics (Available After Phase 22)

The following metrics are planned for integration:

- `trustscale_node_trust_score`
- `trustscale_node_quarantine_count`
- `trustscale_node_discrepancy`
- `trustscale_node_is_quarantined`

---

## Notes

- This document is a planning artifact for Phase 25.
- Grafana dashboard JSON will be created after Phase 22 is completed.
- Current verification confirms that Prometheus and Grafana are operational.