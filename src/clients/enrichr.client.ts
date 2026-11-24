import { EnrichrTerm, RetrievedEvidenceItem } from "../schemas/biological.schema.js";

export class EnrichrClient {
  private readonly baseUrl: string = "https://maayanlab.cloud/Enrichr";
  private readonly timeoutMs: number = 10000;

  /**
   * Run gene set enrichment against Jensen COMPARTMENTS or GO
   */
  public async getEnrichment(
    geneSymbols: string[],
    backgroundType = "Jensen_COMPARTMENTS"
  ): Promise<{ terms: EnrichrTerm[]; evidence: RetrievedEvidenceItem[] }> {
    if (!geneSymbols || geneSymbols.length === 0) {
      return { terms: [], evidence: [] };
    }

    const cleanGenes = geneSymbols
      .map((g) => g.trim().toUpperCase())
      .filter((g) => g.length > 0 && !g.startsWith("MT-")); // Filter mitochondrial reads from pathway query

    if (cleanGenes.length === 0) {
      return { terms: [], evidence: [] };
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      // 1. Submit gene list
      const formData = new FormData();
      formData.append("list", cleanGenes.join("\n"));
      formData.append("description", "Spatial niche marker gene enrichment");

      const addResponse = await fetch(`${this.baseUrl}/addList`, {
        method: "POST",
        body: formData,
        signal: controller.signal
      });

      if (!addResponse.ok) {
        throw new Error(`Enrichr addList HTTP ${addResponse.status}`);
      }

      const addData = (await addResponse.json()) as { userListId: number };
      const userListId = addData.userListId;

      // 2. Fetch enrichment terms
      const enrichUrl = `${this.baseUrl}/enrich?userListId=${userListId}&backgroundType=${backgroundType}`;
      const enrichResponse = await fetch(enrichUrl, { signal: controller.signal });

      clearTimeout(timeoutId);

      if (!enrichResponse.ok) {
        throw new Error(`Enrichr enrich HTTP ${enrichResponse.status}`);
      }

      const enrichData = (await enrichResponse.json()) as Record<string, unknown[][]>;
      let rawHits = enrichData[backgroundType] || [];

      // Fallback to GO_Biological_Process_2023 if 0 hits
      if (rawHits.length === 0 && backgroundType !== "GO_Biological_Process_2023") {
        const fallbackUrl = `${this.baseUrl}/enrich?userListId=${userListId}&backgroundType=GO_Biological_Process_2023`;
        const fallbackRes = await fetch(fallbackUrl);
        if (fallbackRes.ok) {
          const fallbackData = (await fallbackRes.json()) as Record<string, unknown[][]>;
          rawHits = fallbackData["GO_Biological_Process_2023"] || [];
        }
      }

      const terms: EnrichrTerm[] = [];
      const evidence: RetrievedEvidenceItem[] = [];

      for (const h of rawHits.slice(0, 5)) {
        // Enrichr format: [rank, term, p-value, z-score, combined_score, overlapping_genes, adjusted_p]
        const termName = String(h[1]);
        const pVal = Number(h[2]);
        const combined = Number(h[4]);
        const genes = Array.isArray(h[5]) ? (h[5] as string[]) : [];

        terms.push({
          term: termName,
          pValue: pVal,
          adjustedPValue: Number(h[6] || pVal),
          combinedScore: combined,
          overlappingGenes: genes
        });

        evidence.push({
          source: "Enrichr",
          queryTarget: termName,
          content: `Enriched Component: ${termName} (p=${pVal.toExponential(2)}, combined score=${combined.toFixed(1)}). Overlapping genes: ${genes.join(", ")}`,
          url: `https://maayanlab.cloud/Enrichr/enrich?userListId=${userListId}&backgroundType=${backgroundType}`,
          retrievedAt: new Date().toISOString(),
          relevanceScore: Math.min(1.0, combined / 100)
        });
      }

      return { terms, evidence };
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const error = err as Error;
      return {
        terms: [],
        evidence: [
          {
            source: "Enrichr",
            queryTarget: geneSymbols.join(","),
            content: `Enrichr enrichment query failed: ${error.message}`,
            url: "https://maayanlab.cloud/Enrichr",
            retrievedAt: new Date().toISOString(),
            relevanceScore: 0.0
          }
        ]
      };
    }
  }
}
