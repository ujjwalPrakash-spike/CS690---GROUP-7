# Ujjwal Prakash (241111): Web-Augmented NicheAgent & Gemini API Benchmarking

This module contains Ujjwal's contributions to CS690 Group 3:
- **Web-Augmented NicheAgent**: An autonomous computational genomics agent engineered in strict TypeScript and LangGraph.js (`@langchain/langgraph`) that resolves zero-shot LLM hallucinations by querying live public biomedical knowledge bases (MyGene.info, Enrichr, and NCBI PubMed) when multi-signal biological uncertainty triggers fire.
- Dual-granularity schema separation (`anatomicalLayer` vs `predominantCellType`) preventing single-cell ontology bias.
- Mitochondrial and technical read pre-filtering (`MT-` filter).
- Automated Gemini API benchmarking and calibration analysis across STARmap BZ5, MERFISH -0.14, and Visium DLPFC 151673.

### Quick Start
```bash
npm install
npm test          # Runs all 16 Vitest unit tests
npm run build     # Strict TypeScript build (tsc)
```
Full documentation is available in `docs/final_report.md`.
