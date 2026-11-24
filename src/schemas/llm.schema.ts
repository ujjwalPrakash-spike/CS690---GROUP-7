import { z } from "zod";

export const PredictionSchema = z.object({
  nicheLabel: z.string().min(1, "Niche label cannot be empty"),
  anatomicalLayer: z.string().min(1, "Anatomical layer is required (e.g. Layer 1, Layer 2, Layer 3, Layer 4, Layer 5, Layer 6, White Matter)"),
  predominantCellType: z.string().min(1, "Predominant cell type description is required"),
  confidence: z.number().min(0).max(1, "Confidence must be between 0 and 1"),
  reasoning: z.string().min(1, "Reasoning is required"),
  candidateNiches: z.array(z.string()).default([]),
  uncertaintyFactors: z.array(z.string()).default([]),
  keySupportingGenes: z.array(z.string()).default([])
});

export type LLMPrediction = z.infer<typeof PredictionSchema>;

export const UncertaintyAssessmentSchema = z.object({
  isUncertain: z.boolean(),
  uncertaintyScore: z.number().min(0).max(1),
  reasons: z.array(z.string()),
  recommendedQueries: z.array(z.string()).default([]),
  focusGenes: z.array(z.string()).default([]),
  needsPubMedSearch: z.boolean().default(false)
});

export type UncertaintyAssessment = z.infer<typeof UncertaintyAssessmentSchema>;

export const EvidenceEvaluationSchema = z.object({
  supportsInitial: z.boolean(),
  evidenceSummary: z.string(),
  conflictingGenes: z.array(z.string()).default([]),
  suggestedRevision: z.string().nullable().default(null),
  revisedConfidence: z.number().min(0).max(1),
  furtherRetrievalNeeded: z.boolean().default(false)
});

export type EvidenceEvaluation = z.infer<typeof EvidenceEvaluationSchema>;
