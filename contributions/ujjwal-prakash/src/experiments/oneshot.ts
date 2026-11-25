import { EnrichrClient } from "../clients/enrichr.client.js";
import { GeminiClient } from "../clients/gemini.client.js";
import { MyGeneClient } from "../clients/mygene.client.js";
import { PredictionSchema, type LLMPrediction } from "../schemas/llm.schema.js";
import type { GroundTruthNiche, NicheEvaluationResult } from "../types/evaluation.js";
import { evaluatePredictionAgainstGroundTruth } from "./evaluator.js";

/**
 * Condition B: One-Shot RAG
 */
export async function runOneShotRAGNiche(
  niche: GroundTruthNiche,
  geminiClient?: GeminiClient,
  myGeneClient?: MyGeneClient,
  enrichrClient?: EnrichrClient
): Promise<NicheEvaluationResult> {
  const gemini = geminiClient || new GeminiClient();
  const myGene = myGeneClient || new MyGeneClient();
  const enrichr = enrichrClient || new EnrichrClient();
  const startTime = Date.now();

  const focusGenes = niche.markerGenes.filter((g) => !g.startsWith("MT-")).slice(0, 5);

  const [geneEvidence, enrichrResult] = await Promise.all([
    myGene.queryGenes(focusGenes, "human"),
    enrichr.getEnrichment(focusGenes, "Jensen_COMPARTMENTS")
  ]);

  const allEvidence = [...geneEvidence, ...enrichrResult.evidence];
  const evidenceSummary = allEvidence
    .map((e) => `- [${e.source} - ${e.queryTarget}]: ${e.content}`)
    .join("\n");

  const prompt = `
You are an expert computational biologist annotating spatial transcriptomics niches.
Tissue Context: Human Dorsolateral Prefrontal Cortex (DLPFC)
Species: human
Marker Genes (top 10 differential markers from ${niche.method} cluster ${niche.clusterId}):
${niche.markerGenes.map((g, i) => `${i + 1}. ${g}`).join("\n")}

Retrieved External Biological Knowledge:
${evidenceSummary}

Task:
Using both the marker genes and the retrieved external biological knowledge, predict the specific biological niche identity.
Provide both the primary anatomical layer (e.g. "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5", "Layer 6", "White Matter") AND the predominant cell type.
Provide confidence between 0.0 and 1.0, explicit reasoning citing the biological evidence, and key supporting genes.

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

  const estimatedCostUsd = 0.00012;

  return {
    clusterId: niche.clusterId,
    method: niche.method,
    condition: "OneShotRAG",
    predictedLabel: prediction.nicheLabel,
    groundTruthLabel: niche.majorityLayer,
    confidence: prediction.confidence,
    matchCategory: evalScore.matchCategory,
    isConfidentlyWrong: evalScore.isConfidentlyWrong,
    retrievalIterations: 1,
    retrievedEvidenceCount: allEvidence.length,
    latencyMs,
    estimatedCostUsd,
    rationale: `${prediction.reasoning} [Cell Type: ${prediction.predominantCellType}]`,
    evidenceSummary: evidenceSummary.slice(0, 500),
    sourceUrls: allEvidence.map((e) => e.url)
  };
}
