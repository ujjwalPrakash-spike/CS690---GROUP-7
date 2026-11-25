import { buildNicheAgentGraph } from "../graph/builder.js";
import { GeminiClient } from "../clients/gemini.client.js";
import { MyGeneClient } from "../clients/mygene.client.js";
import { EnrichrClient } from "../clients/enrichr.client.js";
import type { GroundTruthNiche, NicheEvaluationResult } from "../types/evaluation.js";
import { evaluatePredictionAgainstGroundTruth } from "./evaluator.js";

/**
 * Condition C: Iterative RAG using LangGraph.js
 * Runs the dynamic state machine:
 * Input validation -> Initial prediction -> Uncertainty assessment ->
 * Conditional biological retrieval -> Evidence evaluation -> Prediction revision -> Final formatting.
 */
export async function runIterativeRAGNiche(
  niche: GroundTruthNiche,
  geminiClient?: GeminiClient,
  myGeneClient?: MyGeneClient,
  enrichrClient?: EnrichrClient
): Promise<NicheEvaluationResult> {
  const startTime = Date.now();

  const app = await buildNicheAgentGraph({
    geminiClient,
    myGeneClient,
    enrichrClient
  });

  const finalState = await app.invoke({
    markerGenes: niche.markerGenes,
    tissue: "Human Dorsolateral Prefrontal Cortex (DLPFC)",
    species: "human",
    clusterId: niche.clusterId,
    upstreamMethod: niche.method,
    maxIterations: 2
  });

  const prediction = finalState.finalPrediction || finalState.initialPrediction || {
    nicheLabel: "Unknown",
    confidence: 0.1,
    reasoning: "Failed to produce prediction",
    candidateNiches: [],
    uncertaintyFactors: [],
    keySupportingGenes: []
  };

  const latencyMs = Date.now() - startTime;
  const evalScore = evaluatePredictionAgainstGroundTruth(
    prediction.nicheLabel,
    prediction.confidence,
    niche
  );

  const iterations = finalState.iterationCount;
  // Estimated cost based on number of Gemini calls (initial, evaluate, revise)
  const callsCount = 1 + (iterations > 0 ? 2 * iterations : 0);
  const estimatedCostUsd = callsCount * 0.0001;

  const sourceUrls = Array.from(new Set(finalState.retrievedEvidence.map((e: { url: string }) => e.url)));

  return {
    clusterId: niche.clusterId,
    method: niche.method,
    condition: "IterativeRAG",
    predictedLabel: prediction.nicheLabel,
    groundTruthLabel: niche.majorityLayer,
    confidence: prediction.confidence,
    matchCategory: evalScore.matchCategory,
    isConfidentlyWrong: evalScore.isConfidentlyWrong,
    retrievalIterations: iterations,
    retrievedEvidenceCount: finalState.retrievedEvidence.length,
    latencyMs,
    estimatedCostUsd,
    rationale: prediction.reasoning,
    evidenceSummary: finalState.evidenceEvaluation?.evidenceSummary,
    sourceUrls
  };
}
