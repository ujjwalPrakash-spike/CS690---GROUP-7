import { z } from "zod";

export const MyGeneHitSchema = z.object({
  query: z.string().optional(),
  symbol: z.string().optional(),
  name: z.string().optional(),
  summary: z.string().optional(),
  type_of_gene: z.string().optional()
});

export type MyGeneHit = z.infer<typeof MyGeneHitSchema>;

export const EnrichrTermSchema = z.object({
  term: z.string(),
  pValue: z.number(),
  adjustedPValue: z.number().optional(),
  combinedScore: z.number(),
  overlappingGenes: z.array(z.string())
});

export type EnrichrTerm = z.infer<typeof EnrichrTermSchema>;

export const RetrievedEvidenceItemSchema = z.object({
  source: z.enum(["MyGene.info", "Enrichr", "PubMed"]),
  queryTarget: z.string(),
  content: z.string(),
  url: z.string().url(),
  retrievedAt: z.string(),
  relevanceScore: z.number().min(0).max(1).default(1.0)
});

export type RetrievedEvidenceItem = z.infer<typeof RetrievedEvidenceItemSchema>;
