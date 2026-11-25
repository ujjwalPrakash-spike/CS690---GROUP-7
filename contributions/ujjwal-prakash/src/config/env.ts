import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const EnvSchema = z.object({
  GEMINI_API_KEY: z.string().min(1, "GEMINI_API_KEY is required"),
  GEMINI_MODEL: z.string().default("gemini-flash-lite-latest"),
  MAX_RETRIEVAL_ITERATIONS: z.coerce.number().int().positive().default(2),
  UNCERTAINTY_THRESHOLD: z.coerce.number().min(0).max(1).default(0.70),
  REQUEST_TIMEOUT_MS: z.coerce.number().int().positive().default(15000),
  MAX_RETRIES: z.coerce.number().int().nonnegative().default(4)
});

export type EnvConfig = z.infer<typeof EnvSchema>;

export function getEnvConfig(): EnvConfig {
  const result = EnvSchema.safeParse(process.env);
  if (!result.success) {
    const issues = result.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join(", ");
    throw new Error(`Environment configuration error: ${issues}`);
  }
  return result.data;
}
