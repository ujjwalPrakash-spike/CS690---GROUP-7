import { StateGraph, START, END } from "@langchain/langgraph";
import { GeminiClient } from "../clients/gemini.client.js";
import { MyGeneClient } from "../clients/mygene.client.js";
import { EnrichrClient } from "../clients/enrichr.client.js";
import { PubMedClient } from "../clients/pubmed.client.js";
import { NicheAgentAnnotation } from "../types/state.js";
import { inputValidatorNode } from "./nodes/inputValidator.js";
import { createInitialPredictorNode } from "./nodes/initialPredictor.js";
import { uncertaintyAssessorNode } from "./nodes/uncertaintyAssessor.js";
import { createBiologicalRetrieverNode } from "./nodes/biologicalRetriever.js";
import { createEvidenceEvaluatorNode } from "./nodes/evidenceEvaluator.js";
import { createPredictionReviserNode } from "./nodes/predictionReviser.js";
import { finalFormatterNode } from "./nodes/finalFormatter.js";
import { routeAfterUncertainty, routeAfterRevision } from "./edges/routing.js";

export interface GraphBuilderOptions {
  geminiClient?: GeminiClient;
  myGeneClient?: MyGeneClient;
  enrichrClient?: EnrichrClient;
  pubMedClient?: PubMedClient;
}

/**
 * Builds and compiles the Web-Augmented NicheAgent LangGraph
 */
export async function buildNicheAgentGraph(options: GraphBuilderOptions = {}) {
  const initialPredictorNode = await createInitialPredictorNode(options.geminiClient);
  const biologicalRetrieverNode = await createBiologicalRetrieverNode(
    options.myGeneClient,
    options.enrichrClient,
    options.pubMedClient
  );
  const evidenceEvaluatorNode = await createEvidenceEvaluatorNode(options.geminiClient);
  const predictionReviserNode = await createPredictionReviserNode(options.geminiClient);

  const workflow = new StateGraph(NicheAgentAnnotation)
    // 1. Nodes
    .addNode("validate", inputValidatorNode)
    .addNode("predict", initialPredictorNode)
    .addNode("assess", uncertaintyAssessorNode)
    .addNode("retrieve", biologicalRetrieverNode)
    .addNode("evaluate", evidenceEvaluatorNode)
    .addNode("revise", predictionReviserNode)
    .addNode("format", finalFormatterNode)

    // 2. Linear initial flow
    .addEdge(START, "validate")
    .addEdge("validate", "predict")
    .addEdge("predict", "assess")

    // 3. Conditional edge after uncertainty assessment
    .addConditionalEdges("assess", routeAfterUncertainty, {
      retrieve: "retrieve",
      format: "format"
    })

    // 4. Evidence processing pipeline
    .addEdge("retrieve", "evaluate")
    .addEdge("evaluate", "revise")

    // 5. Conditional edge after revision
    .addConditionalEdges("revise", routeAfterRevision, {
      retrieve: "retrieve",
      format: "format"
    })

    // 6. Terminal edge
    .addEdge("format", END);

  return workflow.compile();
}
