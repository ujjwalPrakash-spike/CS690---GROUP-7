import { GeminiClient } from "../../clients/gemini.client.js";
import { PredictionSchema, type LLMPrediction } from "../../schemas/llm.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export async function createPredictionReviserNode(client?: GeminiClient) {
  const gemini = client || new GeminiClient();

  return async function predictionReviserNode(
    state: NicheAgentState
  ): Promise<NicheAgentUpdate> {
    const initial = state.initialPrediction;
    const evaluation = state.evidenceEvaluation;
    const evidence = state.retrievedEvidence;

    if (!evaluation || !initial) {
      return {
        executionTrace: ["[PredictionReviser] Skipped revision (missing evaluation or initial prediction)"]
      };
    }

    if (evaluation.supportsInitial && (!evaluation.suggestedRevision || evaluation.suggestedRevision === initial.nicheLabel)) {
      const updated: LLMPrediction = {
        ...initial,
        confidence: Math.max(initial.confidence, evaluation.revisedConfidence),
        reasoning: `${initial.reasoning} Supported by external biological evidence: ${evaluation.evidenceSummary}`
      };
      return {
        revisedPrediction: updated,
        finalPrediction: updated,
        executionTrace: [
          `[PredictionReviser] Confirmed prediction '${updated.nicheLabel}' with calibrated confidence ${updated.confidence.toFixed(2)}`
        ]
      };
    }

    const prompt = `
You are an expert computational biologist synthesizing a revised spatial transcriptomics niche annotation.
Tissue Context: ${state.tissue}
Original Hypothesis: "${initial.nicheLabel}" (Layer: ${initial.anatomicalLayer})
Evidence Assessment: ${evaluation.evidenceSummary}
Suggested Alternative Layer: "${evaluation.suggestedRevision || "None"}"
Conflicting Genes: ${evaluation.conflictingGenes.join(", ")}
All Marker Genes: ${state.markerGenes.join(", ")}

Top Retrieved Biological Facts:
${evidence.slice(-8).map((e) => `- [${e.source}] ${e.queryTarget}: ${e.content}`).join("\n")}

Task:
Produce the final, scientifically defensible biological niche annotation.
RULES:
1. Always set "nicheLabel" to the primary anatomical cortical layer (e.g. "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5", "Layer 6", "White Matter").
2. Set "anatomicalLayer" to the cortical layer.
3. Set "predominantCellType" to the resident cell type (e.g. "Astrocytes / Glia", "Pyramidal neurons", "Infragranular projection neurons", "Oligodendrocytes").
4. If markers are astrocyte/glia dominated in superficial cortex, the anatomical layer is "Layer 1".
5. If markers have neuronal DIRAS2/SLC17A7/SYT1 alongside MBP/PLP1, the anatomical layer is "Layer 6".
6. Assign appropriately calibrated confidence.

Respond strictly in JSON matching this schema:
{
  "nicheLabel": "string (Anatomical layer)",
  "anatomicalLayer": "string",
  "predominantCellType": "string",
  "confidence": number,
  "reasoning": "string",
  "candidateNiches": ["string"],
  "uncertaintyFactors": ["string"],
  "keySupportingGenes": ["string"]
}
`.trim();

    try {
      const revised = await gemini.generateStructured<LLMPrediction>(
        prompt,
        JSON.stringify(PredictionSchema.shape)
      );

      const parsed = PredictionSchema.parse(revised);

      return {
        revisedPrediction: parsed,
        finalPrediction: parsed,
        executionTrace: [
          `[PredictionReviser] Revised prediction from '${initial.nicheLabel}' to '${parsed.nicheLabel}' (${parsed.anatomicalLayer}) (confidence: ${parsed.confidence.toFixed(2)})`
        ]
      };
    } catch (err: unknown) {
      const error = err as Error;
      const fallbackLabel = evaluation.suggestedRevision || initial.nicheLabel;
      const fallback: LLMPrediction = {
        ...initial,
        nicheLabel: fallbackLabel,
        anatomicalLayer: fallbackLabel,
        confidence: evaluation.revisedConfidence,
        reasoning: `Revision heuristic applied: ${evaluation.evidenceSummary}`
      };

      return {
        revisedPrediction: fallback,
        finalPrediction: fallback,
        errors: [`Prediction revision synthesis error: ${error.message}`],
        executionTrace: [
          `[PredictionReviser] Fallback revision applied: '${fallback.nicheLabel}'`
        ]
      };
    }
  };
}
