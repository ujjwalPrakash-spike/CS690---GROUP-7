import { MyGeneHit, MyGeneHitSchema, RetrievedEvidenceItem } from "../schemas/biological.schema.js";

export class MyGeneClient {
  private readonly baseUrl: string = "https://mygene.info/v3";
  private readonly timeoutMs: number = 8000;

  public async queryGenes(
    geneSymbols: string[],
    species = "human"
  ): Promise<RetrievedEvidenceItem[]> {
    if (!geneSymbols || geneSymbols.length === 0) return [];

    const cleanSymbols = geneSymbols
      .map((g) => g.trim().toUpperCase())
      .filter((g) => g.length > 0);

    const params = new URLSearchParams();
    params.append("q", cleanSymbols.join(","));
    params.append("scopes", "symbol");
    params.append("fields", "symbol,name,summary,type_of_gene");
    params.append("species", species);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params.toString(),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`MyGene.info API returned HTTP ${response.status}`);
      }

      const rawItems = (await response.json()) as unknown[];
      const evidenceItems: RetrievedEvidenceItem[] = [];

      for (const item of rawItems) {
        const parsed = MyGeneHitSchema.safeParse(item);
        if (parsed.success) {
          const hit = parsed.data;
          const symbol = hit.symbol || hit.query || "Unknown";
          const desc = hit.summary || hit.name || "Known biological gene";
          evidenceItems.push({
            source: "MyGene.info",
            queryTarget: symbol,
            content: `Gene ${symbol} (${hit.name || "unnamed"}): ${desc}`,
            url: `https://mygene.info/v3/gene/${symbol}`,
            retrievedAt: new Date().toISOString(),
            relevanceScore: 1.0
          });
        }
      }

      return evidenceItems;
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const error = err as Error;
      // Return empty with error provenance rather than crashing pipeline
      return [
        {
          source: "MyGene.info",
          queryTarget: geneSymbols.join(","),
          content: `MyGene.info query failed: ${error.message}`,
          url: "https://mygene.info",
          retrievedAt: new Date().toISOString(),
          relevanceScore: 0.0
        }
      ];
    }
  }
}
