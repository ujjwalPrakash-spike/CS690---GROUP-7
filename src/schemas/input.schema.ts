import { z } from "zod";

export const MarkerGeneStatSchema = z.object({
  gene: z.string().min(1),
  logFoldChange: z.number().optional(),
  pValueAdjusted: z.number().optional(),
  meanExpression: z.number().optional()
});

export type MarkerGeneStat = z.infer<typeof MarkerGeneStatSchema>;

export const NicheInputSchema = z.object({
  markerGenes: z.array(z.string().min(1)).min(1, "At least one marker gene must be provided"),
  tissue: z.string().min(1, "Tissue description is required"),
  species: z.string().default("human"),
  expressionStats: z.array(MarkerGeneStatSchema).optional(),
  clusterId: z.union([z.string(), z.number()]).optional(),
  upstreamMethod: z.enum(["BANKSY", "CellCharter", "PROST", "Other"]).optional()
});

export type NicheInput = z.infer<typeof NicheInputSchema>;
