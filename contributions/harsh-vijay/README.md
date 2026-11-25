# Harsh Vijay (240436): Alternative CosMx Niche Formulations & Multi-Model Benchmarks

This module contains Harsh's contributions to CS690 Group 3:
- Three alternative spatial niche formulations on the CosMx SMI human lung tumour dataset:
  - `m1/`: **Composition Niches** from CLR-transformed neighbourhood cell-state fractions.
  - `m2/`: **Consensus Niches** from spatial co-association graphs across 9 BANKSY parameter configurations plus CellCharter.
  - `m3/`: **Identity + Program + Ligand-Receptor Evidence** filtering out ubiquitous genes and incorporating OmniPath/Squidpy LR interactions.
- Zero-shot benchmarking of Gemini and Mistral on DLPFC niches, and multi-template evaluation of Claude and ChatGPT on STARmap and MERFISH niches.

Each subfolder (`m1/`, `m2/`, `m3/`) contains self-contained notebooks and detailed execution instructions in its respective `README.md`.
