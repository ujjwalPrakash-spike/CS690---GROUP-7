import { getEnvConfig } from "../../config/env.js";
import type { UncertaintyAssessment } from "../../schemas/llm.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export function uncertaintyAssessorNode(state: NicheAgentState): NicheAgentUpdate {
  const config = getEnvConfig();
  const threshold = config.UNCERTAINTY_THRESHOLD;
  const prediction = state.initialPrediction;

  if (!prediction) {
    return {
      uncertainty: {
        isUncertain: true,
        uncertaintyScore: 1.0,
        reasons: ["No initial prediction found"],
        recommendedQueries: state.markerGenes.slice(0, 5),
        focusGenes: state.markerGenes.slice(0, 5),
        needsPubMedSearch: false
      },
      executionTrace: ["[UncertaintyAssessor] Triggered retrieval due to missing prediction"]
    };
  }

  const reasons: string[] = [];
  let uncertaintyScore = 1.0 - prediction.confidence;
  let needsPubMedSearch = false;

  // 1. Confidence threshold check
  if (prediction.confidence < threshold) {
    reasons.push(
      `Confidence (${prediction.confidence.toFixed(2)}) is below threshold (${threshold})`
    );
  }

  // 2. High mitochondrial dominance check
  const mtGenes = state.markerGenes.filter((g) => g.toUpperCase().startsWith("MT-"));
  if (mtGenes.length >= 3) {
    reasons.push(
      `High mitochondrial marker presence (${mtGenes.length} genes) risks metabolic confounding`
    );
    uncertaintyScore = Math.max(uncertaintyScore, 0.4);
  }

  // 3. Known cortical ambiguous markers: Neurofilaments (NEFL, NEFM, NEFH)
  const neurofilamentGenes = state.markerGenes.filter((g) =>
    ["NEFL", "NEFM", "NEFH", "SNCG"].includes(g.toUpperCase())
  );
  if (neurofilamentGenes.length >= 2) {
    reasons.push(
      `Neurofilament marker cluster (${neurofilamentGenes.join(", ")}) spans both Layer 3 pyramidal neurons and Layer 5 projection neurons`
    );
    uncertaintyScore = Math.max(uncertaintyScore, 0.45);
    needsPubMedSearch = true; // Trigger targeted literature check
  }

  // 4. White Matter vs Layer 6 border check: co-presence of MBP/PLP1 and neuronal markers
  const myelinGenes = state.markerGenes.filter((g) => ["MBP", "PLP1", "MOBP", "CNP"].includes(g.toUpperCase()));
  const neuronalGenes = state.markerGenes.filter((g) => ["DIRAS2", "SLC17A7", "SYT1", "GPM6A"].includes(g.toUpperCase()));
  if (myelinGenes.length >= 1 && neuronalGenes.length >= 2) {
    reasons.push(
      `Co-expression of myelin markers (${myelinGenes.join(",")}) and infragranular neuronal markers (${neuronalGenes.join(",")}) indicates potential Layer 6 / White Matter boundary`
    );
    uncertaintyScore = Math.max(uncertaintyScore, 0.4);
  }

  // 5. Multiple candidate niches noted by LLM
  if (prediction.candidateNiches.length > 1) {
    reasons.push(
      `LLM flagged multiple competing candidate niches: ${prediction.candidateNiches.join(", ")}`
    );
  }

  // Focus genes for retrieval: filter out MT- and select the top 5 informative markers
  const focusGenes = state.markerGenes
    .filter((g) => !g.toUpperCase().startsWith("MT-"))
    .slice(0, 5);

  const isUncertain = reasons.length > 0 || uncertaintyScore > 1.0 - threshold;

  const assessment: UncertaintyAssessment = {
    isUncertain,
    uncertaintyScore: Number(uncertaintyScore.toFixed(2)),
    reasons,
    recommendedQueries: focusGenes,
    focusGenes,
    needsPubMedSearch
  };

  return {
    uncertainty: assessment,
    executionTrace: [
      `[UncertaintyAssessor] isUncertain=${isUncertain} (score=${assessment.uncertaintyScore}, pubmed=${needsPubMedSearch}). Reasons: ${reasons.join("; ") || "None (High confidence)"}`
    ]
  };
}
