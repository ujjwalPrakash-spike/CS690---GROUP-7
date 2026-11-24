import { getEnvConfig } from "../config/env.js";

export interface GeminiRequestOptions {
  temperature?: number;
  maxOutputTokens?: number;
  responseMimeType?: string;
  systemInstruction?: string;
}

export class GeminiClient {
  private readonly apiKey: string;
  private readonly model: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;

  constructor(apiKey?: string, model?: string) {
    const config = getEnvConfig();
    this.apiKey = apiKey || config.GEMINI_API_KEY;
    this.model = model || config.GEMINI_MODEL;
    this.timeoutMs = config.REQUEST_TIMEOUT_MS;
    this.maxRetries = 4;
  }

  public async generateContent(
    prompt: string,
    options: GeminiRequestOptions = {}
  ): Promise<string> {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${this.apiKey}`;

    const body: Record<string, unknown> = {
      contents: [
        {
          role: "user",
          parts: [{ text: prompt }]
        }
      ],
      generationConfig: {
        temperature: options.temperature ?? 0.2,
        maxOutputTokens: options.maxOutputTokens ?? 4096,
        responseMimeType: options.responseMimeType ?? "application/json"
      }
    };

    if (options.systemInstruction) {
      body.systemInstruction = {
        parts: [{ text: options.systemInstruction }]
      };
    }

    let attempt = 0;
    while (attempt <= this.maxRetries) {
      attempt++;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(body),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text().catch(() => "");
          const isRateLimit = response.status === 429;
          const isServerUnavailable = response.status === 503 || response.status === 500;

          if ((isRateLimit || isServerUnavailable) && attempt <= this.maxRetries) {
            const backoffMs = Math.min(1500 * Math.pow(2, attempt) + Math.random() * 500, 10000);
            await new Promise((res) => setTimeout(res, backoffMs));
            continue;
          }

          throw new Error(
            `Gemini API HTTP ${response.status} (${response.statusText}): ${errorText.slice(0, 300)}`
          );
        }

        const data = (await response.json()) as {
          candidates?: Array<{
            content?: {
              parts?: Array<{ text?: string }>;
            };
          }>;
        };

        const candidateText = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (!candidateText) {
          throw new Error("Gemini returned empty candidate content");
        }

        return candidateText;
      } catch (err: unknown) {
        clearTimeout(timeoutId);
        const error = err as Error;

        if (attempt <= this.maxRetries) {
          const backoff = 1500 * attempt;
          await new Promise((res) => setTimeout(res, backoff));
          continue;
        }

        throw error;
      }
    }

    throw new Error("Gemini request failed after maximum retries");
  }

  public async generateStructured<T>(
    prompt: string,
    schemaDescription: string,
    options: GeminiRequestOptions = {}
  ): Promise<T> {
    const systemInstruction = `${options.systemInstruction || ""}\nYou are a strict biological genomics reasoner. Return ONLY valid JSON matching this schema: ${schemaDescription}. Do not include markdown code fences (\`\`\`json) if possible, or ensure it parses cleanly.`.trim();

    const rawText = await this.generateContent(prompt, {
      ...options,
      responseMimeType: "application/json",
      systemInstruction
    });

    let cleaned = rawText.trim();
    if (cleaned.startsWith("```")) {
      cleaned = cleaned.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
    }

    try {
      return JSON.parse(cleaned) as T;
    } catch {
      // Robust regex extraction of outermost JSON object
      const match = cleaned.match(/\{[\s\S]*\}/);
      if (match) {
        try {
          return JSON.parse(match[0]) as T;
        } catch {
          // Fall through
        }
      }
      throw new Error(`Failed to parse structured JSON from Gemini response: ${rawText.slice(0, 200)}...`);
    }
  }
}
