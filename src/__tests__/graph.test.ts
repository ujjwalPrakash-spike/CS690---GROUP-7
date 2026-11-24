import { describe, it, expect, vi } from "vitest";
import { buildNicheAgentGraph } from "../graph/builder.js";
import { routeAfterUncertainty, routeAfterRevision } from "../graph/edges/routing.js";
import type { NicheAgentState } from "../types/state.js";
import type { GeminiClient } from "../clients/gemini.client.js";
import type { MyGeneClient } from "../clients/mygene.client.js";
import type { EnrichrClient } from "../clients/enrichr.client.js";
import type { PubMedClient } from "../clients/pubmed.client.js";

describe("LangGraph State Machine Architecture & Routing", () => {
  it("routes to retrieval when uncertain and iterations < maxIterations", () => {
    const state = {
      uncertainty: {
        isUncertain: true,
        uncertaintyScore: 0.7,
        reasons: ["Ambiguous neurofilaments"],
        recommendedQueries: ["NEFL"],
        focusGenes: ["NEFL"],
        needsPubMedSearch: true
      },
      iterationCount: 0,
      maxIterations: 2
    } as unknown as NicheAgentState;

    expect(routeAfterUncertainty(state)).toBe("retrieve");
  });

  it("routes to format when certain or when maxIterations reached", () => {
    const certainState = {
      uncertainty: { isUncertain: false, uncertaintyScore: 0.1, reasons: [], recommendedQueries: [], focusGenes: [] },
      iterationCount: 0,
      maxIterations: 2
    } as unknown as NicheAgentState;
    expect(routeAfterUncertainty(certainState)).toBe("format");

    const maxedState = {
      uncertainty: { isUncertain: true, uncertaintyScore: 0.9, reasons: ["uncertain"], recommendedQueries: [], focusGenes: [] },
      iterationCount: 2,
      maxIterations: 2
    } as unknown as NicheAgentState;
    expect(routeAfterUncertainty(maxedState)).toBe("format");
  });

  it("executes full LangGraph pipeline end-to-end with injected clients", async () => {
    const mockGemini = {
      generateStructured: vi.fn()
        // 1. Initial prediction
        .mockResolvedValueOnce({
          nicheLabel: "Layer 2",
          anatomicalLayer: "Layer 2",
          predominantCellType: "Superficial pyramidal neurons",
          confidence: 0.55,
          reasoning: "Superficial cortical markers present.",
          candidateNiches: ["Layer 2", "Layer 3"],
          uncertaintyFactors: ["Overlapping markers"],
          keySupportingGenes: ["ENC1"]
        })
        // 2. Evidence evaluation
        .mockResolvedValueOnce({
          supportsInitial: false,
          evidenceSummary: "Retrieved facts indicate Layer 3 pyramidal neuron specialization.",
          conflictingGenes: ["ENC1"],
          suggestedRevision: "Layer 3",
          revisedConfidence: 0.88,
          furtherRetrievalNeeded: false
        })
        // 3. Prediction revision
        .mockResolvedValueOnce({
          nicheLabel: "Layer 3",
          anatomicalLayer: "Layer 3",
          predominantCellType: "Layer 3 pyramidal neurons",
          confidence: 0.90,
          reasoning: "Revised to Layer 3 based on retrieved evidence.",
          candidateNiches: ["Layer 3"],
          uncertaintyFactors: [],
          keySupportingGenes: ["ENC1", "HPCAL1"]
        })
    } as unknown as GeminiClient;

    const mockMyGene = {
      queryGenes: vi.fn().mockResolvedValue([
        {
          source: "MyGene.info",
          queryTarget: "ENC1",
          content: "Gene ENC1: Ectodermal-neural cortex 1",
          url: "https://mygene.info/v3/gene/ENC1",
          retrievedAt: new Date().toISOString(),
          relevanceScore: 1.0
        }
      ])
    } as unknown as MyGeneClient;

    const mockEnrichr = {
      getEnrichment: vi.fn().mockResolvedValue({
        terms: [
          {
            term: "Dendrite (GO:0030425)",
            pValue: 0.001,
            combinedScore: 250,
            overlappingGenes: ["ENC1"]
          }
        ],
        evidence: [
          {
            source: "Enrichr",
            queryTarget: "Dendrite",
            content: "Enriched Term: Dendrite (GO:0030425)",
            url: "https://maayanlab.cloud/Enrichr",
            retrievedAt: new Date().toISOString(),
            relevanceScore: 1.0
          }
        ]
      })
    } as unknown as EnrichrClient;

    const mockPubMed = {
      searchLiterature: vi.fn().mockResolvedValue([])
    } as unknown as PubMedClient;

    const graph = await buildNicheAgentGraph({
      geminiClient: mockGemini,
      myGeneClient: mockMyGene,
      enrichrClient: mockEnrichr,
      pubMedClient: mockPubMed
    });

    const finalState = await graph.invoke({
      markerGenes: ["ENC1", "HPCAL1", "CAMK2N1"],
      tissue: "Human Dorsolateral Prefrontal Cortex",
      species: "human",
      maxIterations: 2
    });

    expect(finalState.finalPrediction).toBeDefined();
    expect(finalState.finalPrediction?.nicheLabel).toBe("Layer 3");
    expect(finalState.finalPrediction?.anatomicalLayer).toBe("Layer 3");
    expect(finalState.finalPrediction?.confidence).toBe(0.9);
    expect(finalState.iterationCount).toBe(1);
    expect(finalState.retrievedEvidence.length).toBeGreaterThan(0);
    expect(finalState.executionTrace.length).toBeGreaterThan(5);
  });
});
