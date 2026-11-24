import { describe, it, expect } from "vitest";
import { NicheInputSchema } from "../schemas/input.schema.js";
import { PredictionSchema, UncertaintyAssessmentSchema, EvidenceEvaluationSchema } from "../schemas/llm.schema.js";
import { MyGeneHitSchema, EnrichrTermSchema } from "../schemas/biological.schema.js";

describe("Zod Validation Schemas", () => {
  it("validates valid niche input", () => {
    const input = {
      markerGenes: ["MBP", "PLP1", "MOBP"],
      tissue: "Human DLPFC",
      species: "human",
      clusterId: 4,
      upstreamMethod: "BANKSY" as const
    };
    const parsed = NicheInputSchema.parse(input);
    expect(parsed.markerGenes).toHaveLength(3);
    expect(parsed.species).toBe("human");
  });

  it("rejects empty marker gene array", () => {
    const invalid = {
      markerGenes: [],
      tissue: "Human DLPFC"
    };
    const result = NicheInputSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it("validates dual-granularity LLM prediction schema", () => {
    const prediction = {
      nicheLabel: "Layer 5",
      anatomicalLayer: "Layer 5",
      predominantCellType: "Deep pyramidal neurons",
      confidence: 0.88,
      reasoning: "High expression of PCP4 and synaptic markers indicates deep pyramidal layer 5.",
      candidateNiches: ["Layer 5", "Layer 6"],
      uncertaintyFactors: [],
      keySupportingGenes: ["PCP4", "SNAP25"]
    };
    const parsed = PredictionSchema.parse(prediction);
    expect(parsed.nicheLabel).toBe("Layer 5");
    expect(parsed.anatomicalLayer).toBe("Layer 5");
    expect(parsed.predominantCellType).toBe("Deep pyramidal neurons");
    expect(parsed.confidence).toBe(0.88);
  });

  it("validates uncertainty assessment schema", () => {
    const assessment = {
      isUncertain: true,
      uncertaintyScore: 0.65,
      reasons: ["Neurofilament ambiguity across L3 and L5"],
      recommendedQueries: ["NEFL", "NEFM"],
      focusGenes: ["NEFL", "NEFM"],
      needsPubMedSearch: true
    };
    const parsed = UncertaintyAssessmentSchema.parse(assessment);
    expect(parsed.isUncertain).toBe(true);
    expect(parsed.reasons).toHaveLength(1);
    expect(parsed.needsPubMedSearch).toBe(true);
  });

  it("validates biological API response schemas", () => {
    const geneHit = {
      symbol: "MBP",
      name: "myelin basic protein",
      summary: "Major constituent of the myelin sheath",
      type_of_gene: "protein-coding"
    };
    expect(MyGeneHitSchema.safeParse(geneHit).success).toBe(true);

    const term = {
      term: "Myelin Sheath (GO:0043209)",
      pValue: 0.0001,
      combinedScore: 450.2,
      overlappingGenes: ["MBP", "PLP1"]
    };
    expect(EnrichrTermSchema.safeParse(term).success).toBe(true);
  });
});
