# DLPFC prompts used in the web chats

Each prompt was pasted into ChatGPT and Claude 3 times, each time in a new chat with memory off.
Marker genes are the top 10 Wilcoxon genes per niche from BANKSY and CellCharter on Visium 151673.

## banksy: S1a: name only, no tissue

```
Identify the spatial niche (tissue region) for each row using the following marker genes. Only provide the niche name, one per line, in the format '<row id>: <niche name>'. Some rows can be a mixture of regions.

niche_0: ENC1, CAMK2N1, HPCAL1, HOPX, MT-CO1, MT-ND1, MT-CYB, SERPINE2, MT-ATP6, OLFM1
niche_1: MBP, DIRAS2, PLP1, KRT17, SLC17A7, SYT1, GPM6A, CPE, TMSB10, SCGB2A2
niche_2: NEFL, NEFM, NEFH, SNCG, MT-CO2, SCN1B, TUBA1B, MT-CO3, MT-ATP6, NDUFA4
niche_3: TMSB10, PCP4, SNAP25, TUBA1B, TUBB2A, SYT1, STMN1, SNCB, STMN2, SYN2
niche_4: PLP1, MBP, CRYAB, CNP, GFAP, MOBP, TF, PTGDS, S100B, FTH1
niche_5: MALAT1, CST3, CLU, MT-ND2, MT-ND1, COX6C, SLC1A2, MT-ND3, MT-ND5, GFAP
```

## banksy: S1b: name only, with tissue

```
Identify the spatial niche (tissue region) of human dorsolateral prefrontal cortex for each row using the following marker genes. Only provide the niche name, one per line, in the format '<row id>: <niche name>'. Some rows can be a mixture of regions.

niche_0: ENC1, CAMK2N1, HPCAL1, HOPX, MT-CO1, MT-ND1, MT-CYB, SERPINE2, MT-ATP6, OLFM1
niche_1: MBP, DIRAS2, PLP1, KRT17, SLC17A7, SYT1, GPM6A, CPE, TMSB10, SCGB2A2
niche_2: NEFL, NEFM, NEFH, SNCG, MT-CO2, SCN1B, TUBA1B, MT-CO3, MT-ATP6, NDUFA4
niche_3: TMSB10, PCP4, SNAP25, TUBA1B, TUBB2A, SYT1, STMN1, SNCB, STMN2, SYN2
niche_4: PLP1, MBP, CRYAB, CNP, GFAP, MOBP, TF, PTGDS, S100B, FTH1
niche_5: MALAT1, CST3, CLU, MT-ND2, MT-ND1, COX6C, SLC1A2, MT-ND3, MT-ND5, GFAP
```

## banksy: S2: name + function + confidence

```
These are spatial niches found by clustering a spatial transcriptomics slice of human dorsolateral prefrontal cortex. Each row lists a niche's top differentially expressed marker genes (one-vs-rest, Wilcoxon).

niche_0: ENC1, CAMK2N1, HPCAL1, HOPX, MT-CO1, MT-ND1, MT-CYB, SERPINE2, MT-ATP6, OLFM1
niche_1: MBP, DIRAS2, PLP1, KRT17, SLC17A7, SYT1, GPM6A, CPE, TMSB10, SCGB2A2
niche_2: NEFL, NEFM, NEFH, SNCG, MT-CO2, SCN1B, TUBA1B, MT-CO3, MT-ATP6, NDUFA4
niche_3: TMSB10, PCP4, SNAP25, TUBA1B, TUBB2A, SYT1, STMN1, SNCB, STMN2, SYN2
niche_4: PLP1, MBP, CRYAB, CNP, GFAP, MOBP, TF, PTGDS, S100B, FTH1
niche_5: MALAT1, CST3, CLU, MT-ND2, MT-ND1, COX6C, SLC1A2, MT-ND3, MT-ND5, GFAP

For each niche, say what region it is and what it is doing. Use free text, not a fixed list. If the markers look like technical noise (for example mitochondrial genes) rather than biology, say so and lower the confidence.
Answer only with a JSON array, one object per niche: {"niche_id": "...", "label": "short niche name", "cell_types": ["main cell types present"], "function": "one or two sentences on what this region is doing biologically", "evidence": ["marker gene -> what it indicates"], "confidence": 0-100}
```

## cellcharter: S1a: name only, no tissue

```
Identify the spatial niche (tissue region) for each row using the following marker genes. Only provide the niche name, one per line, in the format '<row id>: <niche name>'. Some rows can be a mixture of regions.

niche_0: DIRAS2, SYT1, TMSB10, MBP, SLC17A7, SNAP25, CHN1, GPM6A, DKK3, KRT17
niche_1: MBP, PLP1, CNP, GFAP, CRYAB, MOBP, TF, PTGDS, S100B, FTH1
niche_2: NEFL, TUBA1B, SNAP25, PCP4, TMSB10, SNCG, NEFM, UCHL1, STMN2, NDUFA4
niche_3: MALAT1, CST3, CLU, MT-ND1, MT-ND2, SLC1A2, MT-ND3, COX6C, MT3, MT-ND5
niche_4: ENC1, HOPX, HPCAL1, CAMK2N1, MT-CO1, SERPINE2, CCK, OLFM1, CYP46A1, MT-CYB
niche_5: MT-ATP6, ENC1, MT-CO1, MT-ND1, MT-CYB, HOPX, YWHAH, MT-CO2, MT-CO3, OLFM1
```

## cellcharter: S1b: name only, with tissue

```
Identify the spatial niche (tissue region) of human dorsolateral prefrontal cortex for each row using the following marker genes. Only provide the niche name, one per line, in the format '<row id>: <niche name>'. Some rows can be a mixture of regions.

niche_0: DIRAS2, SYT1, TMSB10, MBP, SLC17A7, SNAP25, CHN1, GPM6A, DKK3, KRT17
niche_1: MBP, PLP1, CNP, GFAP, CRYAB, MOBP, TF, PTGDS, S100B, FTH1
niche_2: NEFL, TUBA1B, SNAP25, PCP4, TMSB10, SNCG, NEFM, UCHL1, STMN2, NDUFA4
niche_3: MALAT1, CST3, CLU, MT-ND1, MT-ND2, SLC1A2, MT-ND3, COX6C, MT3, MT-ND5
niche_4: ENC1, HOPX, HPCAL1, CAMK2N1, MT-CO1, SERPINE2, CCK, OLFM1, CYP46A1, MT-CYB
niche_5: MT-ATP6, ENC1, MT-CO1, MT-ND1, MT-CYB, HOPX, YWHAH, MT-CO2, MT-CO3, OLFM1
```

## cellcharter: S2: name + function + confidence

```
These are spatial niches found by clustering a spatial transcriptomics slice of human dorsolateral prefrontal cortex. Each row lists a niche's top differentially expressed marker genes (one-vs-rest, Wilcoxon).

niche_0: DIRAS2, SYT1, TMSB10, MBP, SLC17A7, SNAP25, CHN1, GPM6A, DKK3, KRT17
niche_1: MBP, PLP1, CNP, GFAP, CRYAB, MOBP, TF, PTGDS, S100B, FTH1
niche_2: NEFL, TUBA1B, SNAP25, PCP4, TMSB10, SNCG, NEFM, UCHL1, STMN2, NDUFA4
niche_3: MALAT1, CST3, CLU, MT-ND1, MT-ND2, SLC1A2, MT-ND3, COX6C, MT3, MT-ND5
niche_4: ENC1, HOPX, HPCAL1, CAMK2N1, MT-CO1, SERPINE2, CCK, OLFM1, CYP46A1, MT-CYB
niche_5: MT-ATP6, ENC1, MT-CO1, MT-ND1, MT-CYB, HOPX, YWHAH, MT-CO2, MT-CO3, OLFM1

For each niche, say what region it is and what it is doing. Use free text, not a fixed list. If the markers look like technical noise (for example mitochondrial genes) rather than biology, say so and lower the confidence.
Answer only with a JSON array, one object per niche: {"niche_id": "...", "label": "short niche name", "cell_types": ["main cell types present"], "function": "one or two sentences on what this region is doing biologically", "evidence": ["marker gene -> what it indicates"], "confidence": 0-100}
```

