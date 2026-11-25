import { EnrichrClient } from "../../clients/enrichr.client.js";
import { MyGeneClient } from "../../clients/mygene.client.js";
import { PubMedClient } from "../../clients/pubmed.client.js";
import type { RetrievedEvidenceItem } from "../../schemas/biological.schema.js";
import type { NicheAgentState, NicheAgentUpdate } from "../../types/state.js";

export async function createBiologicalRetrieverNode(
  myGeneClient?: MyGeneClient,
  enrichrClient?: EnrichrClient,
  pubMedClient?: PubMedClient
) {
  const myGene = myGeneClient || new MyGeneClient();
  const enrichr = enrichrClient || new EnrichrClient();
  const pubMed = pubMedClient || new PubMedClient();

  return async function biologicalRetrieverNode(
    state: NicheAgentState
  ): Promise<NicheAgentUpdate> {
    const iteration = state.iterationCount + 1;
    // QC Pre-filtering: Ensure we never query MT- genes
    const focusGenes = state.uncertainty?.focusGenes && state.uncertainty.focusGenes.length > 0
      ? state.uncertainty.focusGenes.filter((g) => !g.startsWith("MT-"))
      : state.markerGenes.filter((g) => !g.startsWith("MT-")).slice(0, 5);

    const trace: string[] = [
      `[BiologicalRetriever] Iteration ${iteration}: Querying external biological APIs for QC-filtered genes: ${focusGenes.join(", ")}`
    ];

    const retrievedItems: RetrievedEvidenceItem[] = [];

    try {
      // Parallel fetch from MyGene, Enrichr, and optionally PubMed
      const fetchPromises: Promise<unknown>[] = [
        myGene.queryGenes(focusGenes, state.species),
        enrichr.getEnrichment(focusGenes, "Jensen_COMPARTMENTS")
      ];

      if (state.uncertainty?.needsPubMedSearch) {
        trace.push(`[BiologicalRetriever] Triggered targeted PubMed search for ambiguous markers`);
        fetchPromises.push(pubMed.searchLiterature(focusGenes, "human DLPFC cortical layer"));
      }

      const results = await Promise.all(fetchPromises);
      const geneItems = results[0] as RetrievedEvidenceItem[];
      const enrichmentResult = results[1] as { evidence: RetrievedEvidenceItem[] };

      retrievedItems.push(...geneItems);
      retrievedItems.push(...enrichmentResult.evidence);

      if (results.length > 2) {
        const pubMedItems = results[2] as RetrievedEvidenceItem[];
        retrievedItems.push(...pubMedItems);
        trace.push(`[BiologicalRetriever] Retrieved ${pubMedItems.length} PubMed literature citations`);
      }

      trace.push(
        `[BiologicalRetriever] Successfully retrieved ${geneItems.length} gene summaries and ${enrichmentResult.evidence.length} cellular localization terms`
      );
    } catch (err: unknown) {
      const error = err as Error;
      trace.push(`[BiologicalRetriever] Retrieval encountered an error: ${error.message}`);
      return {
        iterationCount: iteration,
        errors: [`Retrieval iteration ${iteration} error: ${error.message}`],
        executionTrace: trace
      };
    }

    return {
      iterationCount: iteration,
      retrievedEvidence: retrievedItems,
      executionTrace: trace
    };
  };
}
