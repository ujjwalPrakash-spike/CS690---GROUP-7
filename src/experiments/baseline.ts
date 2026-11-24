import { GeminiClient } from "../clients/gemini.client.js";
import { PredictionSchema, type LLMPrediction } from "../schemas/llm.schema.js";
import type { GroundTruthNiche, NicheEvaluationResult } from "../types/evaluation.js";
import { evaluatePredictionAgainstGroundTruth } from "./evaluator.js";

/**
 * Condition A: Baseline Gemini Zero-Shot
 */
export async function runBaselineNiche(
  niche: GroundTruthNiche,
  client?: GeminiClient
): Promise<NicheEvaluationResult> {
  const gemini = client || new GeminiClient();
  const startTime = Date.now();

  const prompt = `
You are an expert computational biologist annotating spatial transcriptomics niches.
Tissue Context: Human Dorsolateral Prefrontal Cortex (DLPFC)
Species: human
Marker Genes (top 10 differential markers from ${niche.method} cluster ${niche.clusterId}):
${niche.markerGenes.map((g, i) => `${i + 1}. ${g}`).join("\n")}

Task:
Predict the biological identity of this niche.
Provide both the primary anatomical layer (e.g. "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5", "Layer 6", "White Matter") AND the predominant cell type.
Provide confidence between 0.0 and 1.0 and detailed reasoning.

Respond strictly in JSON matching this schema:
{
  "nicheLabel": "string (Anatomical layer, e.g. Layer 1, Layer 3, Layer 5, Layer 6, White Matter)",
  "anatomicalLayer": "string",
  "predominantCellType": "string",
  "confidence": number,
  "reasoning": "string",
  "candidateNiches": ["string"],
  "uncertaintyFactors": ["string"],
  "keySupportingGenes": ["string"]
}
`.trim();

  let prediction: LLMPrediction;
  try {
    prediction = await gemini.generateStructured<LLMPrediction>(
      prompt,
      JSON.stringify(PredictionSchema.shape)
    );
  } catch (err: unknown) {
    const error = err as Error;
    prediction = {
      nicheLabel: "Unknown",
      anatomicalLayer: "Unknown",
      predominantCellType: "Unknown",
      confidence: 0.1,
      reasoning: `Error: ${error.message}`,
      candidateNiches: [],
      uncertaintyFactors: [error.message],
      keySupportingGenes: []
    };
  }

  const latencyMs = Date.now() - startTime;
  const evalScore = evaluatePredictionAgainstGroundTruth(
    prediction.nicheLabel,
    prediction.confidence,
    niche
  );

  const estimatedCostUsd = 0.00007;

  return {
    clusterId: niche.clusterId,
    method: niche.method,
    condition: "Baseline",
    predictedLabel: prediction.nicheLabel,
    groundTruthLabel: niche.majorityLayer,
    confidence: prediction.confidence,
    matchCategory: evalScore.matchCategory,
    isConfidentlyWrong: evalScore.isConfidentlyWrong,
    retrievalIterations: 0,
    retrievedEvidenceCount: 0,
    latencyMs,
    estimatedCostUsd,
    rationale: `${prediction.reasoning} [Cell Type: ${prediction.predominantCellType}]`,
    sourceUrls: []
  };
}
