import { Annotation } from "@langchain/langgraph";
import type { MarkerGeneStat } from "../schemas/input.schema.js";
import type {
  LLMPrediction,
  UncertaintyAssessment,
  EvidenceEvaluation
} from "../schemas/llm.schema.js";
import type { RetrievedEvidenceItem } from "../schemas/biological.schema.js";

/**
 * LangGraph Root State Annotation for Web-Augmented NicheAgent
 */
export const NicheAgentAnnotation = Annotation.Root({
  // Input fields
  markerGenes: Annotation<string[]>({
    reducer: (_, update) => update,
    default: () => []
  }),
  tissue: Annotation<string>({
    reducer: (_, update) => update,
    default: () => "Unknown Tissue"
  }),
  species: Annotation<string>({
    reducer: (_, update) => update,
    default: () => "human"
  }),
  expressionStats: Annotation<MarkerGeneStat[]>({
    reducer: (_, update) => update,
    default: () => []
  }),
  clusterId: Annotation<string | number | undefined>({
    reducer: (_, update) => update,
    default: () => undefined
  }),
  upstreamMethod: Annotation<string | undefined>({
    reducer: (_, update) => update,
    default: () => undefined
  }),

  // Agent Reasoning & Pipeline State
  initialPrediction: Annotation<LLMPrediction | null>({
    reducer: (_, update) => update,
    default: () => null
  }),
  uncertainty: Annotation<UncertaintyAssessment | null>({
    reducer: (_, update) => update,
    default: () => null
  }),
  retrievedEvidence: Annotation<RetrievedEvidenceItem[]>({
    reducer: (current, update) => current.concat(update),
    default: () => []
  }),
  evidenceEvaluation: Annotation<EvidenceEvaluation | null>({
    reducer: (_, update) => update,
    default: () => null
  }),
  iterationCount: Annotation<number>({
    reducer: (_, update) => update,
    default: () => 0
  }),
  maxIterations: Annotation<number>({
    reducer: (_, update) => update,
    default: () => 2
  }),
  revisedPrediction: Annotation<LLMPrediction | null>({
    reducer: (_, update) => update,
    default: () => null
  }),
  finalPrediction: Annotation<LLMPrediction | null>({
    reducer: (_, update) => update,
    default: () => null
  }),

  // Logging & Reliability
  errors: Annotation<string[]>({
    reducer: (current, update) => current.concat(update),
    default: () => []
  }),
  executionTrace: Annotation<string[]>({
    reducer: (current, update) => current.concat(update),
    default: () => []
  })
});

export type NicheAgentState = typeof NicheAgentAnnotation.State;
export type NicheAgentUpdate = typeof NicheAgentAnnotation.Update;
