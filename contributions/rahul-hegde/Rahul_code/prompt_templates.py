"""The four prompt templates (T1-T4) sent to Gemini.

Group names are blinded to letters (A-H for the ground-truth regions, A-G for the BANKSY niches),
and neither the clustering method nor the dataset's region names appear in any prompt.
run_gemini.build_prompts fills {TABLE} / {FC_TABLE} and fixes the number of groups.

T1 baseline, T2 + tissue context, T3 + "niche, not cell type", T4 + log2 fold-changes.
"""

HEADER = """You are an expert computational biologist and spatial transcriptomics specialist.
"""

CONTEXT = """- **Modality/Platform:** NanoString CosMx SMI (960-gene panel)
- **Species:** Human
- **Organ / Primary Tissue:** Lung, tumour-bearing
- **Input:** 8 spatially distinct regions of one tissue section, labelled A-H
"""

T1 = HEADER + """
### Task:
Identify and annotate the biological cellular niche (tissue microenvironment
identity) for each region below.

### Metadata:
- **Modality/Platform:** NanoString CosMx SMI (960-gene panel)
- **Number of regions:** 8 (A-H)
- **Target Species:** Human

### Region Marker Genes:
{TABLE}

### Output Format:
For each region, output:
1. **Predicted Niche / Microenvironment:**
2. **Key Characteristic Cell Types:**
3. **Biological Role / Summary:**
"""

T2 = HEADER + """
### Task:
Identify and annotate the biological niche for each region, using marker genes
and explicit tissue context.

### Experimental & Tissue Context:
""" + CONTEXT + """- **Specimen:** FFPE section spanning tumour and adjacent non-malignant lung

### Region Marker Genes:
{TABLE}

### Expected Output:
Map each region to the known compartments of tumour-bearing lung tissue.
Present your findings as a table:
| Region | Predicted Niche | Dominant Cell Types | Marker Evidence |
"""

T3 = HEADER + """
### Task:
Identify the spatial NICHE each region represents. Each region is a tissue area
or microenvironment, NOT a single cell type.

### Experimental & Tissue Context:
""" + CONTEXT + """
### Region Marker Genes:
{TABLE}

### Instructions:
1. Name each region as a REGION or MICROENVIRONMENT, not as a cell type.
   Prefer "macrophage-rich stroma" over "macrophages".
2. Where a region is defined by one dominant infiltrating population, say so
   explicitly and name the surrounding compartment as well.
3. For each region give: predicted niche, the cell populations composing it, and
   the markers that justify the call.
"""

T4 = HEADER + """
### Task:
Identify and annotate spatial niches using ranked differential expression
metrics (Log2 Fold Change).

### Experimental & Tissue Context:
""" + CONTEXT + """
### Region Marker Genes:
{TABLE}

### Log2 Fold Changes (same row order as above):
{FC_TABLE}

### Instructions:
1. Prioritise genes with high enrichment (log2FC >= 1.5-2.0) as definitive
   markers; treat weakly enriched housekeeping-like genes as uninformative.
2. Distinguish tumour/epithelial compartments from stromal, immune and vascular
   niches.
3. For each region give the predicted niche identity, its key functional
   markers, and the compartments you would expect adjacent to it.
"""

TEMPLATES = {"T1": T1, "T2": T2, "T3": T3, "T4": T4}
