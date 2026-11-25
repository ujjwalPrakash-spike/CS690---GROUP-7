import type { RetrievedEvidenceItem } from "../schemas/biological.schema.js";

export class PubMedClient {
  private readonly baseUrl: string = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils";
  private readonly timeoutMs: number = 8000;

  /**
   * Search PubMed for literature on specific gene markers in cortical layers
   */
  public async searchLiterature(
    geneSymbols: string[],
    context = "DLPFC cortical layer"
  ): Promise<RetrievedEvidenceItem[]> {
    if (!geneSymbols || geneSymbols.length === 0) return [];

    const cleanGenes = geneSymbols
      .map((g) => g.trim().toUpperCase())
      .filter((g) => g.length > 0 && !g.startsWith("MT-"));

    if (cleanGenes.length === 0) return [];

    // Construct targeted query: e.g. "(NEFL OR NEFM) AND (cortical layer OR laminar) AND DLPFC"
    const geneClause = cleanGenes.length === 1
      ? cleanGenes[0]
      : `(${cleanGenes.slice(0, 3).join(" OR ")})`;
    const query = encodeURIComponent(`${geneClause} AND (${context})`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      // 1. Search for PMIDs
      const searchUrl = `${this.baseUrl}/esearch.fcgi?db=pubmed&term=${query}&retmode=json&retmax=2`;
      const searchRes = await fetch(searchUrl, { signal: controller.signal });
      if (!searchRes.ok) throw new Error(`PubMed esearch HTTP ${searchRes.status}`);

      const searchData = (await searchRes.json()) as {
        esearchresult?: { idlist?: string[] };
      };
      const ids = searchData.esearchresult?.idlist || [];
      if (ids.length === 0) {
        clearTimeout(timeoutId);
        return [];
      }

      // 2. Fetch summaries for PMIDs
      const summaryUrl = `${this.baseUrl}/esummary.fcgi?db=pubmed&id=${ids.join(",")}&retmode=json`;
      const summaryRes = await fetch(summaryUrl, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!summaryRes.ok) throw new Error(`PubMed esummary HTTP ${summaryRes.status}`);

      const summaryData = (await summaryRes.json()) as {
        result?: Record<string, { title?: string; source?: string; pubdate?: string }>;
      };

      const evidenceItems: RetrievedEvidenceItem[] = [];
      const resultObj = summaryData.result || {};

      for (const id of ids) {
        const item = resultObj[id];
        if (item && item.title) {
          evidenceItems.push({
            source: "PubMed",
            queryTarget: cleanGenes.join("/"),
            content: `PubMed Literature (PMID: ${id}): "${item.title}". Source: ${item.source || "Journal"} (${item.pubdate || ""}). Relevant to laminar localization of ${cleanGenes.join(", ")}.`,
            url: `https://pubmed.ncbi.nlm.nih.gov/${id}/`,
            retrievedAt: new Date().toISOString(),
            relevanceScore: 0.95
          });
        }
      }

      return evidenceItems;
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const error = err as Error;
      return [
        {
          source: "PubMed",
          queryTarget: geneSymbols.join(","),
          content: `PubMed query failed: ${error.message}`,
          url: "https://pubmed.ncbi.nlm.nih.gov",
          retrievedAt: new Date().toISOString(),
          relevanceScore: 0.0
        }
      ];
    }
  }
}
