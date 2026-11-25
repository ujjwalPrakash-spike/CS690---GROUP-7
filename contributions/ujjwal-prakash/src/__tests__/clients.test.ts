import { describe, it, expect } from "vitest";
import { MyGeneClient } from "../clients/mygene.client.js";
import { EnrichrClient } from "../clients/enrichr.client.js";

describe("Biological Knowledge API Clients", () => {
  it("queries MyGene.info and extracts structured evidence", async () => {
    const client = new MyGeneClient();
    const evidence = await client.queryGenes(["MBP", "PLP1"], "human");

    expect(evidence.length).toBeGreaterThanOrEqual(1);
    const mbpEvidence = evidence.find((e) => e.queryTarget.toUpperCase() === "MBP");
    expect(mbpEvidence).toBeDefined();
    expect(mbpEvidence?.content.toLowerCase()).toContain("myelin");
    expect(mbpEvidence?.url).toContain("mygene.info");
  });

  it("queries Enrichr for cellular component enrichment", async () => {
    const client = new EnrichrClient();
    const result = await client.getEnrichment(["MBP", "PLP1", "MOBP", "CNP"], "GO_Cellular_Component_2023");

    expect(result.evidence.length).toBeGreaterThanOrEqual(1);
    const hasMyelinOrCytoskeleton = result.evidence.some(
      (e) => e.content.toLowerCase().includes("myelin") || e.content.toLowerCase().includes("filament") || e.content.toLowerCase().includes("membrane")
    );
    expect(hasMyelinOrCytoskeleton).toBe(true);
  });
});
