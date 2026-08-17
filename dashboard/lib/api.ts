import type {
  ExperimentSummary,
  NodeTrustDetails,
  ScenarioConfig,
  ScenarioResult,
  BehaviorMode,
  RoutingStrategy,
} from "./types";

const LB_URL = process.env.NEXT_PUBLIC_LB_URL || "http://localhost:8000";
const ORCHESTRATOR_URL =
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || "http://localhost:8200";

const NODE_PORT_MAP: Record<string, number> = {
  node_1: 8001,
  node_2: 8002,
  node_3: 8003,
  node_4: 8004,
  node_5: 8005,
  node_6: 8006,
  node_7: 8007,
  node_8: 8008,
};

function getNodeUrl(nodeId: string): string {
  const port = NODE_PORT_MAP[nodeId];
  if (!port) throw new Error(`Unknown node: ${nodeId}`);
  return `http://localhost:${port}`;
}

async function fetchJson<T>(
  url: string,
  options?: RequestInit,
  retries = 2,
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(options?.headers || {}),
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < retries) {
        await new Promise((resolve) =>
          setTimeout(resolve, 500 * (attempt + 1)),
        );
      }
    }
  }

  throw lastError || new Error("Request failed after retries");
}

export const api = {
  async listNodes(): Promise<string[]> {
    const data = await fetchJson<{ nodes: string[] }>(`${LB_URL}/nodes`);
    return data.nodes;
  },

  async getNodeTrust(nodeId: string): Promise<NodeTrustDetails> {
    return fetchJson<NodeTrustDetails>(`${LB_URL}/nodes/${nodeId}/trust`);
  },

  async sendWork(intensity = 200, count = 1): Promise<void> {
    const requests = Array.from({ length: count }, () =>
      fetchJson(`${LB_URL}/work`, {
        method: "POST",
        body: JSON.stringify({
          task: "dashboard",
          data: "user_traffic",
          intensity,
        }),
      }).catch(() => null),
    );
    await Promise.all(requests);
  },

  async setNodeBehavior(
    nodeId: string,
    mode: BehaviorMode,
    intensity = 0.5,
  ): Promise<void> {
    await fetchJson(`${getNodeUrl(nodeId)}/admin/set-behavior`, {
      method: "POST",
      body: JSON.stringify({ mode, intensity }),
    });
  },

  async resetAllNodes(nodeIds: string[]): Promise<void> {
    await Promise.all(
      nodeIds.map((id) =>
        this.setNodeBehavior(id, "honest", 0.0).catch(() => null),
      ),
    );
  },

  async setRoutingStrategy(strategy: RoutingStrategy): Promise<void> {
    await fetchJson(`${LB_URL}/admin/set-strategy`, {
      method: "POST",
      body: JSON.stringify({ strategy }),
    });
  },

  async getRoutingStrategy(): Promise<RoutingStrategy> {
    const data = await fetchJson<{ strategy: RoutingStrategy }>(
      `${LB_URL}/admin/strategy`,
    );
    return data.strategy;
  },

  async listScenarios(): Promise<ScenarioConfig[]> {
    const data = await fetchJson<{ scenarios: ScenarioConfig[] }>(
      `${ORCHESTRATOR_URL}/scenarios`,
    );
    return data.scenarios;
  },

  async runScenario(scenarioId: string, repetition = 1): Promise<void> {
    await fetchJson(`${ORCHESTRATOR_URL}/scenarios/run`, {
      method: "POST",
      body: JSON.stringify({
        scenario_id: scenarioId,
        repetition_number: repetition,
      }),
    });
  },

  async listExperiments(): Promise<ExperimentSummary[]> {
    const data = await fetchJson<{ experiments: ExperimentSummary[] }>(
      `${ORCHESTRATOR_URL}/experiments`,
    );
    return data.experiments;
  },

  async getExperiment(
    scenarioId: string,
    fileName: string,
  ): Promise<ScenarioResult> {
    return fetchJson<ScenarioResult>(
      `${ORCHESTRATOR_URL}/experiments/${scenarioId}/${fileName}`,
    );
  },

  async listTrains(): Promise<any[]> {
    return fetchJson<any[]>(`${LB_URL}/api/trains`);
  },

  async bookTicket(
    trainId: string,
    passengerName: string,
    seatClass: string = "SL",
  ): Promise<any> {
    return fetchJson(`${LB_URL}/api/book`, {
      method: "POST",
      body: JSON.stringify({
        train_id: trainId,
        passenger_name: passengerName,
        seat_class: seatClass,
      }),
    });
  },
};