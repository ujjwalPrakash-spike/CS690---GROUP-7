# Web-Augmented NicheAgent

Web-Augmented NicheAgent is an autonomous computational biology framework built with LangGraph.js and TypeScript. It annotates spatial transcriptomics niches from differential marker genes using iterative retrieval-augmented generation (RAG) backed by live, public biological databases (MyGene.info, Enrichr, and NCBI PubMed).

---

## 1. Setup and Installation

### Prerequisites
- Node.js (v18.0.0 or higher; tested on v24.12.0)
- npm (v9.0.0 or higher; tested on v11.21.3)
- A Google Gemini API Key (obtained from Google AI Studio)

### Step 1: Clone the Repository
```bash
git clone https://github.com/ujjwalPrakash-spike/langraph-rag-niche-marker.git
cd langraph-rag-niche-marker
```

### Step 2: Install Dependencies
```bash
npm install
```

### Step 3: Configure Environment Variables
Copy the sample environment file to create your local `.env`:
```bash
cp .env.example .env
```

Open `.env` in any editor and set your Gemini API key:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
MAX_RETRIEVAL_ITERATIONS=2
UNCERTAINTY_THRESHOLD=0.70
REQUEST_TIMEOUT_MS=15000
MAX_RETRIES=4
```

Note: No API keys are required for MyGene.info, Enrichr, or NCBI PubMed. Those services are open-access public scientific APIs and are queried directly by the agent over HTTPS.

### Step 4: Run Type Checks and Unit Tests
To verify that all TypeScript types compile strictly and that all 16 automated tests pass:
```bash
# Type check without emitting files
npm run lint

# Run full Vitest suite (schemas, clients, LangGraph routing)
npm test

# Compile TypeScript to dist/
npm run build
```

---

## 2. How to Run the System

### Running the Full Benchmark
To run the automated 3-condition benchmark across all 12 spatial niches from the 10x Visium Human DLPFC dataset:
```bash
npm run benchmark
```
This executes:
1. Condition A: Baseline Gemini Zero-Shot
2. Condition B: One-Shot Static RAG
3. Condition C: Iterative LangGraph Agent

Results are printed to the console as a formatted summary table and saved to `docs/benchmark_results.json`.

### Annotating Custom Gene Lists Programmatically
You can invoke the compiled graph in any Node.js / TypeScript script:

```typescript
import { buildNicheAgentGraph } from "./src/graph/builder.js";

async function annotateNiche() {
  const agent = await buildNicheAgentGraph();

  const result = await agent.invoke({
    markerGenes: ["ENC1", "HPCAL1", "CAMK2N1", "HOPX"],
    tissue: "Human Dorsolateral Prefrontal Cortex (DLPFC)",
    species: "human",
    maxIterations: 2
  });

  console.log("Predicted Layer:", result.finalPrediction?.nicheLabel);
  console.log("Cell Type:", result.finalPrediction?.predominantCellType);
  console.log("Confidence:", result.finalPrediction?.confidence);
  console.log("Reasoning:", result.finalPrediction?.reasoning);
}

annotateNiche();
```

---

## 3. What We Are Doing Here

### The Scientific Problem
In spatial transcriptomics (ST), unsupervised clustering algorithms partition tissue into spatial clusters ("niches"). A persistent bottleneck is assigning reliable biological or anatomical labels to these clusters (for example, identifying whether a cluster represents neocortical Layer 3, Layer 6, or White Matter).

Traditionally, researchers either:
1. Manually inspect marker genes against reference atlases.
2. Rely on zero-shot LLMs, which suffer from severe hallucinations when presented with marker genes alone (e.g. confusing superficial Layer 3 with deep Layer 5 due to shared neurofilament chains, or mistaking astrocytes for non-brain tissues).
3. Use closed-world prototype matching (such as original NicheAgent), which depends on pre-compiled "NicheCards" with fixed expression centroids and cannot generalize to novel tissues or uncurated domains.

### The Proposed Solution
Web-Augmented NicheAgent addresses this limitation by transforming zero-shot LLM prediction into a stateful, iterative agent workflow implemented with LangGraph.js:
- Rather than guessing in a single prompt, the system forms a preliminary hypothesis using a dual-granularity schema (separating anatomical layer from resident cell type).
- An Uncertainty Assessor evaluates confidence, checks for border/myelin mixing, and detects ambiguous marker clusters (such as neurofilaments or high mitochondrial reads).
- When uncertainty is detected, the agent autonomously queries live, external biological APIs:
  - MyGene.info API: Retrieves official gene nomenclature, full protein names, and NCBI RefSeq functional summaries.
  - Enrichr API: Computes cellular component enrichment over the Jensen COMPARTMENTS ontology to determine subcellular localization (e.g., myelin sheath vs. dendritic spines).
  - NCBI PubMed API: Performs targeted biomedical literature searches (via E-utilities) to resolve tissue-specific marker ambiguities.
- An Evidence Evaluator cross-references retrieved biological facts against the hypothesis and refines the prediction under a bounded loop (maximum of 2 iterations).

---

## 4. Benchmark Dataset and Ground Truth

The benchmark targets the canonical 10x Visium Human Dorsolateral Prefrontal Cortex (DLPFC) dataset (Sample 151673; Maynard et al., Nature Neuroscience 2021):
- 3,611 spatial spots across 7 expert-curated ground-truth laminae (Layer 1, Layer 2, Layer 3, Layer 4, Layer 5, Layer 6, and White Matter).
- Two unsupervised spatial clustering algorithms:
  - BANKSY: Incorporates cell-autonomous expression and spatial neighborhood mean gradients (yields 6 niches).
  - CellCharter: Employs variational autoencoder (scVI) latent space embeddings pooled across spatial neighbors (yields 6 niches).
- Differential expression: One-vs-rest Wilcoxon rank-sum tests extracting the top 10 selective marker genes per niche.

---

## 5. Measured Benchmark Results

All 12 authentic spatial niches (6 BANKSY + 6 CellCharter) were benchmarked across the three experimental conditions:

| Metric | Condition A: Baseline Gemini | Condition B: One-Shot RAG | Condition C: Iterative RAG (LangGraph) |
| :--- | :---: | :---: | :---: |
| Total Evaluations | 12 | 12 | 12 |
| Exact Match Rate | 75.00% (9/12) | 66.67% (8/12) | **91.67% (11/12)** |
| Partial Match Rate | 0.00% (0/12) | 0.00% (0/12) | **8.33% (1/12)** |
| Overall Biological Concordance | 75.00% (9/12) | 66.67% (8/12) | **100.00% (12/12)** |
| Severe Mismatch Rate | 25.00% (3/12) | 33.33% (4/12) | **0.00% (0/12)** |
| Confidently Wrong Rate | 25.00% (3/12) | 33.33% (4/12) | **0.00% (0/12)** |
| Expected Calibration Error (ECE) | 0.1458 | 0.2083 | **0.0017** |
| Mean Latency per Niche | 2.19 s | 4.73 s | 7.35 s |
| Total Cost for 12 Niches (USD) | $0.00084 | $0.00144 | $0.00360 |

### Key Scientific Findings:
1. Resolution of Boundary Niches: On CellCharter Cluster 0 (Layer 6, 72.2% spots), Baseline and One-Shot RAG misclassified the cluster as superficial cortex (Layer 3/4). The Iterative Agent retrieved deep infragranular neuronal markers (DIRAS2, SLC17A7), overturned its hypothesis, and correctly predicted Layer 6.
2. Breaking the Neurofilament Trap: For BANKSY Cluster 2 (Layer 3), baseline models misclassified the niche as Layer 5 due to prominent NEFL/NEFM/NEFH expression. Targeted PubMed literature retrieval revealed that large superficial Layer 3 pyramidal neurons express significant neurofilament chains in human DLPFC, allowing the agent to correctly assign Layer 3.
3. Dual-Granularity Calibration: Distinguishing anatomical layers from resident cell types prevented astrocyte-dominated superficial niches from being labeled as non-cortical glia, achieving exact Layer 1 classification.

---

## 6. Project Architecture

```
src/
├── clients/
│   ├── enrichr.client.ts      # Enrichr REST API client (Jensen COMPARTMENTS)
│   ├── gemini.client.ts       # Gemini API client with backoff and JSON repair
│   ├── mygene.client.ts       # MyGene.info batch query client
│   └── pubmed.client.ts       # NCBI E-utilities PubMed client
├── config/
│   └── env.ts                 # Validated environment configuration (Zod)
├── experiments/
│   ├── baseline.ts            # Condition A: Zero-shot LLM runner
│   ├── dataset.ts             # 12 authentic Visium DLPFC niches + ground truth
│   ├── evaluator.ts           # Exact/partial/mismatch scoring engine & calibration
│   ├── iterative.ts           # Condition C: Iterative LangGraph runner
│   ├── oneshot.ts             # Condition B: One-shot static RAG runner
│   └── run_benchmark.ts       # Master benchmark execution script
├── graph/
│   ├── builder.ts             # LangGraph state machine assembly and compilation
│   ├── edges/
│   │   └── routing.ts         # Conditional routing logic
│   └── nodes/
│       ├── biologicalRetriever.ts # Parallel API fetch node
│       ├── evidenceEvaluator.ts   # Fact verification node
│       ├── finalFormatter.ts      # Formatted response with provenance URLs
│       ├── initialPredictor.ts    # Dual-granularity prediction node
│       ├── inputValidator.ts      # QC filter node (strips MT- reads)
│       ├── predictionReviser.ts   # Evidence synthesis and revision node
│       └── uncertaintyAssessor.ts # Uncertainty diagnosis node
├── schemas/
│   ├── biological.schema.ts   # Zod contracts for MyGene, Enrichr, PubMed
│   ├── input.schema.ts        # Zod input validation schemas
│   └── llm.schema.ts          # Zod schemas for dual predictions and evaluations
├── types/
│   ├── evaluation.ts          # Benchmark metric interfaces
│   └── state.ts               # LangGraph state annotation and reducers
└── index.ts                   # Library exports
```

---

## 7. Reports and Figures

- Project Context Audit: `docs/project_context.md`
- Comprehensive Final Report: `docs/final_report.md`
- Raw Benchmark Results (JSON): `docs/benchmark_results.json`
- Accuracy Breakdown Chart: `docs/figures/benchmark_accuracy_breakdown.png`
- Hallucination and Calibration Chart: `docs/figures/benchmark_hallucination_calibration.png`
- Pipeline Architecture Diagram: `docs/figures/pipeline_architecture.png`
- Execution Latency Chart: `docs/figures/benchmark_latency.png`

---

## 8. License

This project is developed for CS690 Computational Genomics course research. All external APIs used (MyGene.info, Enrichr, NCBI E-utilities) are public domain research infrastructure.
