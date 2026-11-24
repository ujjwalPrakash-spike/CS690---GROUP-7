import type { NicheAgentState } from "../../types/state.js";

/**
 * Conditional routing after uncertainty assessment
 */
export function routeAfterUncertainty(state: NicheAgentState): "retrieve" | "format" {
  const isUncertain = state.uncertainty?.isUncertain ?? false;
  const canIterate = state.iterationCount < state.maxIterations;

  if (isUncertain && canIterate) {
    return "retrieve";
  }
  return "format";
}

/**
 * Conditional routing after prediction revision
 */
export function routeAfterRevision(state: NicheAgentState): "retrieve" | "format" {
  const needsMore = state.evidenceEvaluation?.furtherRetrievalNeeded ?? false;
  const canIterate = state.iterationCount < state.maxIterations;

  if (needsMore && canIterate) {
    return "retrieve";
  }
  return "format";
}
