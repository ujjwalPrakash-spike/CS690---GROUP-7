import { describe, it, expect } from "vitest";
import {
  normalizeLayerString,
  evaluatePredictionAgainstGroundTruth,
  computeBenchmarkSummary
} from "../experiments/evaluator.js";
import type { GroundTruthNiche, NicheEvaluationResult } from "../types/evaluation.js";

describe("Benchmark Evaluation Logic", () => {
  const sampleNiche: GroundTruthNiche = {
    clusterId: 0,
    method: "BANKSY",
    markerGenes: ["ENC1", "HPCAL1"],
    majorityLayer: "Layer 3",
    minorLayers: [{ layer: "Layer 2", proportion: 0.28 }],
    spotCounts: { Layer1: 0, Layer2: 213, Layer3: 545, Layer4: 0, Layer5: 0, Layer6: 0, WM: 0 },
    totalSpots: 758
  };

  it("normalizes diverse layer naming conventions", () => {
    expect(normalizeLayerString("Human Cortical Layer 3")).toBe("Layer 3");
    expect(normalizeLayerString("Layer III pyramidal neurons")).toBe("Layer 3");
    expect(normalizeLayerString("Layer 2/3 cortical boundary")).toBe("Layer 2/3");
    expect(normalizeLayerString("Cerebral White Matter")).toBe("White Matter");
    expect(normalizeLayerString("WM")).toBe("White Matter");
  });

  it("scores exact match when naming majority layer", () => {
    const res = evaluatePredictionAgainstGroundTruth("Layer 3", 0.85, sampleNiche);
    expect(res.matchCategory).toBe("exact");
    expect(res.isConfidentlyWrong).toBe(false);
  });

  it("scores transitional layer matching as exact when minor proportion >= 10%", () => {
    const res = evaluatePredictionAgainstGroundTruth("Layer 2/3", 0.8, sampleNiche);
    expect(res.matchCategory).toBe("exact");
  });

  it("scores minor layer only as partial match", () => {
    const res = evaluatePredictionAgainstGroundTruth("Layer 2", 0.65, sampleNiche);
    expect(res.matchCategory).toBe("partial");
    expect(res.isConfidentlyWrong).toBe(false);
  });

  it("scores wrong layer as mismatch and flags confident error", () => {
    const res = evaluatePredictionAgainstGroundTruth("Layer 5", 0.95, sampleNiche);
    expect(res.matchCategory).toBe("mismatch");
    expect(res.isConfidentlyWrong).toBe(true);
  });

  it("computes aggregate benchmark summary metrics correctly", () => {
    const results: NicheEvaluationResult[] = [
      {
        clusterId: 0,
        method: "BANKSY",
        condition: "Baseline",
        predictedLabel: "Layer 3",
        groundTruthLabel: "Layer 3",
        confidence: 0.9,
        matchCategory: "exact",
        isConfidentlyWrong: false,
        retrievalIterations: 0,
        retrievedEvidenceCount: 0,
        latencyMs: 1200,
        estimatedCostUsd: 0.0001,
        rationale: "test",
        sourceUrls: []
      },
      {
        clusterId: 1,
        method: "BANKSY",
        condition: "Baseline",
        predictedLabel: "Layer 1",
        groundTruthLabel: "Layer 6",
        confidence: 0.85,
        matchCategory: "mismatch",
        isConfidentlyWrong: true,
        retrievalIterations: 0,
        retrievedEvidenceCount: 0,
        latencyMs: 1100,
        estimatedCostUsd: 0.0001,
        rationale: "test",
        sourceUrls: []
      }
    ];

    const summary = computeBenchmarkSummary("Baseline", results);
    expect(summary.totalEvaluations).toBe(2);
    expect(summary.exactMatchRate).toBe(0.5);
    expect(summary.mismatchRate).toBe(0.5);
    expect(summary.confidentlyWrongCount).toBe(1);
    expect(summary.confidentlyWrongRate).toBe(0.5);
    expect(summary.meanConfidence).toBe(0.875);
  });
});
