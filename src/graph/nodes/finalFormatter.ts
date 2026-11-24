import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";
import type { LLMPrediction } from "../../schemas/llm.schema.js";

export function finalFormatterNode(state: NicheAgentState): NicheAgentUpdate {
  const prediction = state.finalPrediction || state.revisedPrediction || state.initialPrediction;

  if (!prediction) {
    const fallback: LLMPrediction = {
      nicheLabel: "Unknown",
      anatomicalLayer: "Unknown",
      predominantCellType: "Unknown",
      confidence: 0.0,
      reasoning: "No valid prediction could be formed.",
      candidateNiches: [],
      uncertaintyFactors: ["Graph execution reached termination without prediction"],
      keySupportingGenes: []
    };
    return {
      finalPrediction: fallback,
      executionTrace: ["[FinalFormatter] Output fallback unknown prediction"]
    };
  }

  const traceMsg = `[FinalFormatter] Final prediction: '${prediction.nicheLabel}' (Layer: ${prediction.anatomicalLayer}, Cell: ${prediction.predominantCellType}, Confidence: ${prediction.confidence.toFixed(2)}, Iterations: ${state.iterationCount}, Evidence items: ${state.retrievedEvidence.length})`;

  return {
    finalPrediction: prediction,
    executionTrace: [traceMsg]
  };
}
