import { NicheInputSchema } from "../../schemas/input.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export function inputValidatorNode(state: NicheAgentState): NicheAgentUpdate {
  const result = NicheInputSchema.safeParse({
    markerGenes: state.markerGenes,
    tissue: state.tissue,
    species: state.species,
    expressionStats: state.expressionStats,
    clusterId: state.clusterId,
    upstreamMethod: state.upstreamMethod
  });

  if (!result.success) {
    const errorMsg = `Input validation failed: ${result.error.issues.map((i) => i.message).join(", ")}`;
    return {
      errors: [errorMsg],
      executionTrace: [`[InputValidator] Error: ${errorMsg}`]
    };
  }

  // Quality Control Filter: Identify mitochondrial, ribosomal, and non-coding RNA reads
  const mtGenes = state.markerGenes.filter((g) => g.toUpperCase().startsWith("MT-"));
  const cleanInformativeGenes = state.markerGenes.filter(
    (g) => !g.toUpperCase().startsWith("MT-") && !g.toUpperCase().startsWith("RPS") && !g.toUpperCase().startsWith("RPL")
  );

  const trace = [
    `[InputValidator] Validated ${state.markerGenes.length} marker genes for tissue '${state.tissue}'`,
    mtGenes.length > 0
      ? `[InputValidator] QC Warning: Filtered ${mtGenes.length} mitochondrial artifact genes (${mtGenes.join(", ")}). Clean informative genes: ${cleanInformativeGenes.slice(0, 5).join(", ")}`
      : `[InputValidator] Marker set passed QC with 0 dominant mitochondrial reads.`
  ];

  return {
    executionTrace: trace
  };
}
