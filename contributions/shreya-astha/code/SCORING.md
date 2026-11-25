# How the results in this folder are scored

We use two levels, so that methods which name clusters and methods which label single cells can be compared.

## 1. Label level (an LLM names a cluster or a region)

The expert label of a cluster is the expert region that holds most of its cells, read from the
cluster-by-region crosstab. Each answer gets one grade:

| Grade | Rule |
|---|---|
| Exact | names the majority region; any other region it names is adjacent or holds at least 10% of the cluster |
| Partial | names only a minority region (at least 10%) or an adjacent one, names the right region plus an unrelated one, or is correct but too broad (cell types only, "grey matter") |
| Miss | wrong structure (for example hippocampus for cortex), only wrong regions, or a broad answer that excludes the majority region |

We report the share of Exact, Partial and Miss answers, a 95% Wilson interval for the Exact rate, and
consistency (the share of cluster x prompt x model combinations whose repeats all got the same grade).
Used for: the DLPFC web-chat runs (ChatGPT, Claude), the Gemini API prompt strategies on BANKSY / PROST
clusters, and the CosMx expert-region templates T1-T5.

## 2. Cell level (every cell ends up with a region)

Methods that label cells directly (LLMiniST, NicheAgent-style, M1-M3) are compared with the expert
annotation cell by cell. A cluster name can be scored the same way by giving it to every cell of the cluster.

- accuracy, adjusted Rand index (ARI) and normalised mutual information (NMI)
- 95% bootstrap interval for each, from 2,000 resamples of cells
- McNemar's exact test for two methods on the same cells
- oracle-named accuracy: accuracy after giving each predicted region its best possible name
  (Hungarian matching). The gap to the real accuracy is the naming error, separate from the grouping error.
  This uses labels, so it is a diagnostic only.
