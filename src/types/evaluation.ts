import type { LLMPrediction } from "../schemas/llm.schema.js";

export type MatchCategory = "exact" | "partial" | "mismatch";

export interface GroundTruthNiche {
  clusterId: number | string;
  method: "BANKSY" | "CellCharter";
  markerGenes: string[];
  majorityLayer: string;
  minorLayers: { layer: string; proportion: number }[];
  spotCounts: Record<string, number>;
  totalSpots: number;
}

export interface NicheEvaluationResult {
  clusterId: number | string;
  method: string;
  condition: "Baseline" | "OneShotRAG" | "IterativeRAG";
  predictedLabel: string;
  groundTruthLabel: string;
  confidence: number;
  matchCategory: MatchCategory;
  isConfidentlyWrong: boolean;
  retrievalIterations: number;
  retrievedEvidenceCount: number;
  latencyMs: number;
  estimatedCostUsd: number;
  rationale: string;
  evidenceSummary?: string;
  sourceUrls: string[];
}

export interface ConditionBenchmarkSummary {
  condition: "Baseline" | "OneShotRAG" | "IterativeRAG";
  totalEvaluations: number;
  exactMatchCount: number;
  exactMatchRate: number;
  partialMatchCount: number;
  partialMatchRate: number;
  mismatchCount: number;
  mismatchRate: number;
  confidentlyWrongCount: number;
  confidentlyWrongRate: number;
  meanConfidence: number;
  meanConfidenceOnCorrect: number;
  meanConfidenceOnWrong: number;
  expectedCalibrationError: number;
  meanLatencyMs: number;
  totalCostUsd: number;
}
