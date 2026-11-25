import { GeminiClient } from "../../clients/gemini.client.js";
import { PredictionSchema, type LLMPrediction } from "../../schemas/llm.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export async function createInitialPredictorNode(client?: GeminiClient) {
  const gemini = client || new GeminiClient();

  return async function initialPredictorNode(
    state: NicheAgentState
  ): Promise<NicheAgentUpdate> {
    // QC Pre-filtering: Prioritize clean nuclear genes over MT- reads
    const cleanGenes = state.markerGenes.filter((g) => !g.toUpperCase().startsWith("MT-"));
    const primaryGenes = cleanGenes.length >= 3 ? cleanGenes : state.markerGenes;

    const prompt = `
You are an expert computational genomics pathologist annotating spatial transcriptomics niches.
Tissue Context: ${state.tissue}
Species: ${state.species}
Marker Genes (top differential markers):
${state.markerGenes.map((g, i) => `${i + 1}. ${g} ${g.startsWith("MT-") ? "(mitochondrial read - ignore for layer call)" : ""}`).join("\n")}
Top Informative Nuclear Markers: ${primaryGenes.slice(0, 6).join(", ")}

Task:
Identify the precise anatomical cortical layer and the resident cell type.
CRITICAL NEUROANATOMICAL PRINCIPLES FOR HUMAN DORSOLATERAL PREFRONTAL CORTEX (DLPFC):
1. ANATOMICAL LAYER VS. CELL TYPE: Always provide both the specific cortical layer ("Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5", "Layer 6", or "White Matter") AND the predominant cell type.
2. LAYER 1 (MOLECULAR LAYER): Layer 1 is cell-sparse and dominated by astrocyte processes, microglia, and glia (marked by GFAP, CST3, CLU, SLC1A2, MALAT1). If markers are primarily astrocytic/glial without deep neuronal markers, the anatomical layer is "Layer 1".
3. LAYER 6 VS WHITE MATTER: Layer 6 directly borders White Matter. It often contains passing myelinated fibers (MBP, PLP1), but uniquely expresses cortical neuronal markers (DIRAS2, SLC17A7, SYT1, GPM6A). Pure White Matter lacks excitatory neuronal markers (SLC17A7, SYT1, DIRAS2).
4. LAYER 3 VS LAYER 5: Layer 3 pyramidal neurons express ENC1, HPCAL1, CAMK2N1, and also express neurofilaments (NEFL, NEFM). True Layer 5 is marked by PCP4.
5. Set "nicheLabel" to the primary anatomical layer (e.g. "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5", "Layer 6", "White Matter").

Respond strictly in JSON matching this schema:
{
  "nicheLabel": "string (Anatomical layer, e.g. Layer 1, Layer 3, Layer 5, Layer 6, White Matter)",
  "anatomicalLayer": "string",
  "predominantCellType": "string",
  "confidence": number (0.0 to 1.0),
  "reasoning": "string",
  "candidateNiches": ["string"],
  "uncertaintyFactors": ["string"],
  "keySupportingGenes": ["string"]
}
`.trim();

    try {
      const prediction = await gemini.generateStructured<LLMPrediction>(
        prompt,
        JSON.stringify(PredictionSchema.shape)
      );

      const parsed = PredictionSchema.parse(prediction);
      return {
        initialPrediction: parsed,
        finalPrediction: parsed,
        executionTrace: [
          `[InitialPredictor] Predicted: '${parsed.nicheLabel}' (${parsed.anatomicalLayer} - ${parsed.predominantCellType}) with confidence ${parsed.confidence.toFixed(2)}`
        ]
      };
    } catch (err: unknown) {
      const error = err as Error;
      const fallback: LLMPrediction = {
        nicheLabel: "Unknown Niche",
        anatomicalLayer: "Unknown",
        predominantCellType: "Unknown",
        confidence: 0.1,
        reasoning: `Prediction failed due to error: ${error.message}`,
        candidateNiches: [],
        uncertaintyFactors: [error.message],
        keySupportingGenes: []
      };

      return {
        initialPrediction: fallback,
        finalPrediction: fallback,
        errors: [`Initial prediction error: ${error.message}`],
        executionTrace: [`[InitialPredictor] Error generating prediction: ${error.message}`]
      };
    }
  };
}
