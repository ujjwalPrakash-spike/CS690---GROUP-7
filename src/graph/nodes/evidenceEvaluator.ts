import { GeminiClient } from "../../clients/gemini.client.js";
import { EvidenceEvaluationSchema, type EvidenceEvaluation } from "../../schemas/llm.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export async function createEvidenceEvaluatorNode(client?: GeminiClient) {
  const gemini = client || new GeminiClient();

  return async function evidenceEvaluatorNode(
    state: NicheAgentState
  ): Promise<NicheAgentUpdate> {
    const initial = state.initialPrediction;
    const evidence = state.retrievedEvidence;

    if (!evidence || evidence.length === 0) {
      return {
        executionTrace: ["[EvidenceEvaluator] No retrieved evidence available to evaluate"]
      };
    }

    const evidenceSummaryText = evidence
      .slice(-10)
      .map((e, idx) => `[Evidence ${idx + 1}] (${e.source} - ${e.queryTarget}): ${e.content}`)
      .join("\n");

    const prompt = `
You are an expert genomics reasoning agent evaluating retrieved biological evidence.
Tissue Context: ${state.tissue}
Initial Hypothesis: "${initial?.nicheLabel || "Unknown"}" (Layer: ${initial?.anatomicalLayer || "Unknown"}, Cell: ${initial?.predominantCellType || "Unknown"})
Marker Genes: ${state.markerGenes.join(", ")}

Retrieved External Biological Knowledge:
${evidenceSummaryText}

Task:
Assess whether the retrieved biological facts support the initial predicted niche, or whether they indicate an alternative cortical layer or cell identity.
CRITICAL EVALUATION PRINCIPLES:
1. LAYER 1 VS CELL TYPE: If markers are predominantly astrocytic/glial (GFAP, CST3, CLU, SLC1A2), the anatomical layer is "Layer 1". Do not mislabel Layer 1 as "Astrocytes" or "White Matter".
2. LAYER 6 VS WHITE MATTER: If markers include deep neuronal genes (DIRAS2, SLC17A7, SYT1) alongside MBP/PLP1, the niche is cortical "Layer 6" (which contains infragranular neurons and passing myelinated axons). True White Matter lacks neuronal marker SLC17A7/SYT1.
3. NEUROFILAMENTS (NEFL, NEFM): Note that while NEFL is prominent in Layer 5, large superficial pyramidal neurons in Layer 3 of human DLPFC also express significant NEFL/NEFM. If true Layer 5 marker PCP4 is absent, consider Layer 3.

Respond strictly in JSON matching this schema:
{
  "supportsInitial": boolean,
  "evidenceSummary": "string",
  "conflictingGenes": ["string"],
  "suggestedRevision": "string or null (e.g. Layer 1, Layer 3, Layer 6)",
  "revisedConfidence": number (between 0.0 and 1.0),
  "furtherRetrievalNeeded": boolean
}
`.trim();

    try {
      const evaluation = await gemini.generateStructured<EvidenceEvaluation>(
        prompt,
        JSON.stringify(EvidenceEvaluationSchema.shape)
      );

      const parsed = EvidenceEvaluationSchema.parse(evaluation);

      return {
        evidenceEvaluation: parsed,
        executionTrace: [
          `[EvidenceEvaluator] Evaluated evidence. Supports initial: ${parsed.supportsInitial}. Suggested revision: '${parsed.suggestedRevision || "None"}'. Revised confidence: ${parsed.revisedConfidence.toFixed(2)}`
        ]
      };
    } catch (err: unknown) {
      const error = err as Error;
      return {
        errors: [`Evidence evaluation error: ${error.message}`],
        executionTrace: [`[EvidenceEvaluator] Error evaluating evidence: ${error.message}`]
      };
    }
  };
}
