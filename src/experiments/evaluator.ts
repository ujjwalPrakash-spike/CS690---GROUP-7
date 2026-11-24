import type {
  ConditionBenchmarkSummary,
  GroundTruthNiche,
  MatchCategory,
  NicheEvaluationResult
} from "../types/evaluation.js";

/**
 * Normalizes text string to canonical layer representation using strict word boundaries
 */
export function normalizeLayerString(label: string): string {
  const s = label.trim();

  // 1. Check joint / transitional layers first
  if (/\blayer\s*(2\s*[\/-]\s*3|ii\s*[\/-]\s*iii)\b/i.test(s) || /\bl2[\/-]l?3\b/i.test(s)) {
    return "Layer 2/3";
  }

  // 2. White Matter
  if (/\b(white\s*matter|wm)\b/i.test(s)) {
    return "White Matter";
  }

  // 3. Layer 6 (VI)
  if (/\blayer\s*(6|vi)\b/i.test(s) || /\bl6\b/i.test(s)) {
    return "Layer 6";
  }

  // 4. Layer 5 (V)
  if (/\blayer\s*(5|v)\b/i.test(s) || /\bl5\b/i.test(s)) {
    return "Layer 5";
  }

  // 5. Layer 4 (IV)
  if (/\blayer\s*(4|iv)\b/i.test(s) || /\bl4\b/i.test(s)) {
    return "Layer 4";
  }

  // 6. Layer 3 (III)
  if (/\blayer\s*(3|iii)\b/i.test(s) || /\bl3\b/i.test(s)) {
    return "Layer 3";
  }

  // 7. Layer 2 (II)
  if (/\blayer\s*(2|ii)\b/i.test(s) || /\bl2\b/i.test(s)) {
    return "Layer 2";
  }

  // 8. Layer 1 (I)
  if (/\blayer\s*(1|i)\b/i.test(s) || /\bl1\b/i.test(s)) {
    return "Layer 1";
  }

  return s;
}

/**
 * Evaluates prediction against ground truth niche using course project benchmark criteria
 */
export function evaluatePredictionAgainstGroundTruth(
  predictedRaw: string,
  confidence: number,
  groundTruth: GroundTruthNiche
): { matchCategory: MatchCategory; isConfidentlyWrong: boolean; normalizedPrediction: string } {
  const normPred = normalizeLayerString(predictedRaw);
  const normTruth = normalizeLayerString(groundTruth.majorityLayer);

  // Exact match criteria:
  // Names majority layer directly, or names joint transitional layers (e.g. "Layer 2/3" where L2 holds >=10%)
  const hasExactMajority = normPred.toLowerCase().includes(normTruth.toLowerCase());
  const isTransitionalMatch =
    normPred.includes("Layer 2/3") &&
    (normTruth === "Layer 3" || normTruth === "Layer 2") &&
    groundTruth.minorLayers.some((m) => m.layer === "Layer 2" && m.proportion >= 0.1);

  let matchCategory: MatchCategory = "mismatch";

  if (hasExactMajority || isTransitionalMatch) {
    matchCategory = "exact";
  } else {
    // Check for partial match (minor layer >= 10% or broad cortical descriptor)
    const matchesMinor = groundTruth.minorLayers.some(
      (minor) =>
        minor.proportion >= 0.1 &&
        normPred.toLowerCase().includes(normalizeLayerString(minor.layer).toLowerCase())
    );
    const isBroadCortical =
      normPred.toLowerCase().includes("cortex") ||
      normPred.toLowerCase().includes("cortical") ||
      normPred.toLowerCase().includes("neuron");

    if (matchesMinor || isBroadCortical) {
      matchCategory = "partial";
    } else {
      matchCategory = "mismatch";
    }
  }

  // Confidently wrong criteria: mismatch with confidence >= 0.70
  const isConfidentlyWrong = matchCategory === "mismatch" && confidence >= 0.7;

  return {
    matchCategory,
    isConfidentlyWrong,
    normalizedPrediction: normPred
  };
}

/**
 * Calculates aggregate benchmark summary across evaluations
 */
export function computeBenchmarkSummary(
  condition: "Baseline" | "OneShotRAG" | "IterativeRAG",
  results: NicheEvaluationResult[]
): ConditionBenchmarkSummary {
  const total = results.length;
  if (total === 0) {
    return {
      condition,
      totalEvaluations: 0,
      exactMatchCount: 0,
      exactMatchRate: 0,
      partialMatchCount: 0,
      partialMatchRate: 0,
      mismatchCount: 0,
      mismatchRate: 0,
      confidentlyWrongCount: 0,
      confidentlyWrongRate: 0,
      meanConfidence: 0,
      meanConfidenceOnCorrect: 0,
      meanConfidenceOnWrong: 0,
      expectedCalibrationError: 0,
      meanLatencyMs: 0,
      totalCostUsd: 0
    };
  }

  const exactMatches = results.filter((r) => r.matchCategory === "exact");
  const partialMatches = results.filter((r) => r.matchCategory === "partial");
  const mismatches = results.filter((r) => r.matchCategory === "mismatch");
  const confidentlyWrong = results.filter((r) => r.isConfidentlyWrong);

  const meanConf = results.reduce((acc, r) => acc + r.confidence, 0) / total;
  const meanConfCorrect =
    exactMatches.length > 0
      ? exactMatches.reduce((acc, r) => acc + r.confidence, 0) / exactMatches.length
      : 0;
  const meanConfWrong =
    mismatches.length > 0
      ? mismatches.reduce((acc, r) => acc + r.confidence, 0) / mismatches.length
      : 0;

  const meanLatency = results.reduce((acc, r) => acc + r.latencyMs, 0) / total;
  const totalCost = results.reduce((acc, r) => acc + r.estimatedCostUsd, 0);

  // Expected Calibration Error (ECE) with 5 bins (0-0.2, 0.2-0.4, ..., 0.8-1.0)
  const numBins = 5;
  let ece = 0;
  for (let b = 0; b < numBins; b++) {
    const binMin = b / numBins;
    const binMax = (b + 1) / numBins;
    const binItems = results.filter((r) => r.confidence >= binMin && r.confidence < binMax);
    if (binItems.length > 0) {
      const binAcc = binItems.filter((r) => r.matchCategory === "exact").length / binItems.length;
      const binConf = binItems.reduce((acc, r) => acc + r.confidence, 0) / binItems.length;
      ece += (binItems.length / total) * Math.abs(binAcc - binConf);
    }
  }

  return {
    condition,
    totalEvaluations: total,
    exactMatchCount: exactMatches.length,
    exactMatchRate: Number((exactMatches.length / total).toFixed(4)),
    partialMatchCount: partialMatches.length,
    partialMatchRate: Number((partialMatches.length / total).toFixed(4)),
    mismatchCount: mismatches.length,
    mismatchRate: Number((mismatches.length / total).toFixed(4)),
    confidentlyWrongCount: confidentlyWrong.length,
    confidentlyWrongRate: Number((confidentlyWrong.length / total).toFixed(4)),
    meanConfidence: Number(meanConf.toFixed(4)),
    meanConfidenceOnCorrect: Number(meanConfCorrect.toFixed(4)),
    meanConfidenceOnWrong: Number(meanConfWrong.toFixed(4)),
    expectedCalibrationError: Number(ece.toFixed(4)),
    meanLatencyMs: Math.round(meanLatency),
    totalCostUsd: Number(totalCost.toFixed(6))
  };
}
