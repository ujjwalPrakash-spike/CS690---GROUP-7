import type { GroundTruthNiche } from "../types/evaluation.js";

/**
 * Authentic 10x Visium Human DLPFC sample 151673 Niches
 * Derived from BANKSY / CellCharter clustering and Maynard et al. 2021 manual annotations.
 */
export const DLPFC_BENCHMARK_NICHES: GroundTruthNiche[] = [
  // --- BANKSY NICHES ---
  {
    clusterId: 0,
    method: "BANKSY",
    markerGenes: [
      "ENC1",
      "CAMK2N1",
      "HPCAL1",
      "HOPX",
      "MT-CO1",
      "MT-ND1",
      "MT-CYB",
      "SERPINE2",
      "MT-ATP6",
      "OLFM1"
    ],
    majorityLayer: "Layer 3",
    minorLayers: [{ layer: "Layer 2", proportion: 0.275 }],
    spotCounts: { Layer1: 16, Layer2: 213, Layer3: 545, Layer4: 0, Layer5: 0, Layer6: 0, WM: 0 },
    totalSpots: 774
  },
  {
    clusterId: 1,
    method: "BANKSY",
    markerGenes: [
      "MBP",
      "DIRAS2",
      "PLP1",
      "KRT17",
      "SLC17A7",
      "SYT1",
      "GPM6A",
      "CPE",
      "TMSB10",
      "SCGB2A2"
    ],
    majorityLayer: "Layer 6",
    minorLayers: [{ layer: "Layer 5", proportion: 0.136 }],
    spotCounts: { Layer1: 2, Layer2: 0, Layer3: 0, Layer4: 0, Layer5: 103, Layer6: 628, WM: 24 },
    totalSpots: 757
  },
  {
    clusterId: 2,
    method: "BANKSY",
    markerGenes: [
      "NEFL",
      "NEFM",
      "NEFH",
      "SNCG",
      "MT-CO2",
      "SCN1B",
      "TUBA1B",
      "MT-CO3",
      "MT-ATP6",
      "NDUFA4"
    ],
    majorityLayer: "Layer 3",
    minorLayers: [{ layer: "Layer 4", proportion: 0.274 }],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 441, Layer4: 177, Layer5: 27, Layer6: 0, WM: 0 },
    totalSpots: 645
  },
  {
    clusterId: 3,
    method: "BANKSY",
    markerGenes: [
      "TMSB10",
      "PCP4",
      "SNAP25",
      "TUBA1B",
      "TUBB2A",
      "SYT1",
      "STMN1",
      "SNCB",
      "STMN2",
      "SYN2"
    ],
    majorityLayer: "Layer 5",
    minorLayers: [],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 0, Layer4: 41, Layer5: 542, Layer6: 13, WM: 0 },
    totalSpots: 596
  },
  {
    clusterId: 4,
    method: "BANKSY",
    markerGenes: [
      "PLP1",
      "MBP",
      "CRYAB",
      "CNP",
      "GFAP",
      "MOBP",
      "TF",
      "PTGDS",
      "S100B",
      "FTH1"
    ],
    majorityLayer: "White Matter",
    minorLayers: [],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 0, Layer4: 0, Layer5: 0, Layer6: 51, WM: 489 },
    totalSpots: 540
  },
  {
    clusterId: 5,
    method: "BANKSY",
    markerGenes: [
      "MALAT1",
      "CST3",
      "CLU",
      "MT-ND2",
      "MT-ND1",
      "COX6C",
      "SLC1A2",
      "MT-ND3",
      "MT-ND5",
      "GFAP"
    ],
    majorityLayer: "Layer 1",
    minorLayers: [{ layer: "Layer 2", proportion: 0.134 }],
    spotCounts: { Layer1: 255, Layer2: 40, Layer3: 3, Layer4: 0, Layer5: 1, Layer6: 0, WM: 0 },
    totalSpots: 299
  },

  // --- CELLCHARTER NICHES ---
  {
    clusterId: 0,
    method: "CellCharter",
    markerGenes: [
      "DIRAS2",
      "SYT1",
      "TMSB10",
      "MBP",
      "SLC17A7",
      "SNAP25",
      "CHN1",
      "GPM6A",
      "DKK3",
      "KRT17"
    ],
    majorityLayer: "Layer 6",
    minorLayers: [{ layer: "Layer 5", proportion: 0.278 }],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 0, Layer4: 0, Layer5: 213, Layer6: 554, WM: 0 },
    totalSpots: 767
  },
  {
    clusterId: 1,
    method: "CellCharter",
    markerGenes: [
      "MBP",
      "PLP1",
      "CNP",
      "GFAP",
      "CRYAB",
      "MOBP",
      "TF",
      "PTGDS",
      "S100B",
      "FTH1"
    ],
    majorityLayer: "White Matter",
    minorLayers: [{ layer: "Layer 6", proportion: 0.21 }],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 0, Layer4: 0, Layer5: 0, Layer6: 136, WM: 513 },
    totalSpots: 649
  },
  {
    clusterId: 2,
    method: "CellCharter",
    markerGenes: [
      "NEFL",
      "TUBA1B",
      "SNAP25",
      "PCP4",
      "TMSB10",
      "SNCG",
      "NEFM",
      "UCHL1",
      "STMN2",
      "NDUFA4"
    ],
    majorityLayer: "Layer 5",
    minorLayers: [
      { layer: "Layer 3", proportion: 0.35 },
      { layer: "Layer 4", proportion: 0.181 }
    ],
    spotCounts: { Layer1: 0, Layer2: 0, Layer3: 320, Layer4: 165, Layer5: 426, Layer6: 2, WM: 0 },
    totalSpots: 913
  },
  {
    clusterId: 3,
    method: "CellCharter",
    markerGenes: [
      "MALAT1",
      "CST3",
      "CLU",
      "MT-ND1",
      "MT-ND2",
      "SLC1A2",
      "MT-ND3",
      "COX6C",
      "MT3",
      "MT-ND5"
    ],
    majorityLayer: "Layer 1",
    minorLayers: [{ layer: "Layer 2", proportion: 0.256 }],
    spotCounts: { Layer1: 267, Layer2: 92, Layer3: 0, Layer4: 0, Layer5: 0, Layer6: 0, WM: 0 },
    totalSpots: 359
  },
  {
    clusterId: 4,
    method: "CellCharter",
    markerGenes: [
      "ENC1",
      "HOPX",
      "HPCAL1",
      "CAMK2N1",
      "MT-CO1",
      "SERPINE2",
      "CCK",
      "OLFM1",
      "CYP46A1",
      "MT-CYB"
    ],
    majorityLayer: "Layer 3",
    minorLayers: [{ layer: "Layer 2", proportion: 0.236 }],
    spotCounts: { Layer1: 0, Layer2: 118, Layer3: 382, Layer4: 0, Layer5: 0, Layer6: 0, WM: 0 },
    totalSpots: 500
  },
  {
    clusterId: 5,
    method: "CellCharter",
    markerGenes: [
      "MT-ATP6",
      "ENC1",
      "MT-CO1",
      "MT-ND1",
      "MT-CYB",
      "HOPX",
      "YWHAH",
      "MT-CO2",
      "MT-CO3",
      "OLFM1"
    ],
    majorityLayer: "Layer 3",
    minorLayers: [
      { layer: "Layer 4", proportion: 0.125 },
      { layer: "Layer 2", proportion: 0.102 }
    ],
    spotCounts: { Layer1: 6, Layer2: 43, Layer3: 287, Layer4: 53, Layer5: 34, Layer6: 0, WM: 0 },
    totalSpots: 423
  }
];
