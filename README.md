# CS690: Computational Genomics (2026) — Group 3 Final Project

## Project: Can LLMs Name a Niche? Zero-Shot Biological Labeling from Marker Genes Alone

**Team Members:**
- Rahul Rajesh Hegde (240831)
- Ujjwal Prakash (241111)
- Shreya Astha (240997)
- Harsh Vijay (240436)

**Project Mentor:** Hamim Zafar

---

## Repository Structure & Contributions

This repository is organized into four self-contained contribution modules under `contributions/`:

```
cs690/
├── README.md                               # Project-wide documentation and overview
└── contributions/
    ├── rahul-hegde/                        # Rahul Rajesh Hegde (240831)
    │   ├── README.md
    │   └── Rahul_code/                     # Upstream clustering (BANKSY, CellCharter, PROST)
    │                                       # and CosMx Gemini API prompt benchmarking
    ├── harsh-vijay/                        # Harsh Vijay (240436)
    │   ├── README.md
    │   ├── m1/                             # M1: Composition niches
    │   ├── m2/                             # M2: Consensus spatial co-association
    │   └── m3/                             # M3: Identity + program + ligand-receptor evidence
    ├── shreya-astha/                       # Shreya Astha (240997)
    │   ├── README.md
    │   └── code/                           # Chat LLM benchmark scoring & CardEM cell-level annotation
    └── ujjwal-prakash/                     # Ujjwal Prakash (241111)
        ├── README.md
        ├── src/                            # Web-Augmented NicheAgent (TypeScript & LangGraph.js)
        ├── docs/                           # Empirical benchmark results and schemas
        └── tests/                          # 16/16 Vitest unit tests
```

---

## Module Overview

### 1. Spatial Clustering & Upstream Marker Extraction (`contributions/rahul-hegde/`)
- Upstream niche detection using **BANKSY**, **CellCharter**, and **PROST** across four benchmark spatial transcriptomics platforms (Visium DLPFC, CosMx SMI, MERFISH, STARmap).
- One-vs-rest Wilcoxon differential expression for extracting top-10 marker genes.
- Automated prompt generation (T1–T4) and Gemini API evaluation pipeline for CosMx SMI niches.

### 2. Alternative CosMx Formulations & Cross-Model Benchmarking (`contributions/harsh-vijay/`)
- Formulation **M1 (Composition)**: CLR-transformed neighbourhood cell-state clustering.
- Formulation **M2 (Consensus)**: Multi-parameter BANKSY + CellCharter co-association graph.
- Formulation **M3 (Identity + Program + LR)**: Ubiquitous gene filtering, within-state program markers, and ligand–receptor pairs.
- Multi-model evaluation of Gemini, Mistral, Claude, and ChatGPT across multiple prompt templates on DLPFC, STARmap, and MERFISH.

### 3. Chat LLM Alignment & CardEM Cell-Level Annotation (`contributions/shreya-astha/`)
- Automated grading engine (Exact / Partial / Miss) with 95% Wilson confidence intervals.
- Evaluation of ChatGPT (GPT-5.6 Luna) and Claude (Sonnet 5.5) across 216 scored DLPFC answers.
- **CardEM**: Cluster-free cell-level annotation via LLM reference cards, MAP-EM fitting with Dirichlet priors, and Potts spatial smoothing.

### 4. Web-Augmented NicheAgent (`contributions/ujjwal-prakash/`)
- A stateful **LangGraph.js** agent engineered in strict **TypeScript** that resolves zero-shot hallucinations by dynamically gating retrieval from **MyGene.info**, **Enrichr**, and **NCBI PubMed** APIs.
- Multi-signal biological uncertainty assessment, dual-granularity schema output, and mitochondrial read pre-filtering.
- Achieves **91.67% exact match**, **100.0% biological concordance**, and **0.0% confident hallucinations** on Visium DLPFC.
