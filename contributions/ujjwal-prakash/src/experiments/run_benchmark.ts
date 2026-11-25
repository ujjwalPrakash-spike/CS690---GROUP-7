import fs from "fs";
import path from "path";
import { DLPFC_BENCHMARK_NICHES } from "./dataset.js";
import { runBaselineNiche } from "./baseline.js";
import { runOneShotRAGNiche } from "./oneshot.js";
import { runIterativeRAGNiche } from "./iterative.js";
import { computeBenchmarkSummary } from "./evaluator.js";
import type { NicheEvaluationResult } from "../types/evaluation.js";

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runFullBenchmark() {
  console.log("================================================================================");
  console.log("   CS690 SPATIAL TRANSCRIPTOMICS BENCHMARK: WEB-AUGMENTED NICHEAGENT");
  console.log("   Dataset: 10x Visium Human DLPFC (Sample 151673)");
  console.log("   Niches: 12 (6 BANKSY + 6 CellCharter)");
  console.log("   Conditions: A) Baseline Gemini, B) One-Shot RAG, C) Iterative LangGraph RAG");
  console.log("================================================================================\n");

  const resultsBaseline: NicheEvaluationResult[] = [];
  const resultsOneShot: NicheEvaluationResult[] = [];
  const resultsIterative: NicheEvaluationResult[] = [];

  const totalNiches = DLPFC_BENCHMARK_NICHES.length;

  for (let i = 0; i < totalNiches; i++) {
    const niche = DLPFC_BENCHMARK_NICHES[i];
    console.log(`[${i + 1}/${totalNiches}] Evaluating ${niche.method} Cluster ${niche.clusterId} (Ground Truth: ${niche.majorityLayer})...`);

    // 1. Condition A: Baseline Gemini
    try {
      console.log(`  -> Running Condition A (Baseline Gemini)...`);
      const resA = await runBaselineNiche(niche);
      resultsBaseline.push(resA);
      console.log(`     Pred: '${resA.predictedLabel}' (${resA.matchCategory}, conf: ${resA.confidence.toFixed(2)})`);
    } catch (err: unknown) {
      console.error(`     Error Baseline: ${(err as Error).message}`);
    }
    await sleep(1500);

    // 2. Condition B: One-Shot RAG
    try {
      console.log(`  -> Running Condition B (One-Shot RAG)...`);
      const resB = await runOneShotRAGNiche(niche);
      resultsOneShot.push(resB);
      console.log(`     Pred: '${resB.predictedLabel}' (${resB.matchCategory}, conf: ${resB.confidence.toFixed(2)})`);
    } catch (err: unknown) {
      console.error(`     Error One-Shot: ${(err as Error).message}`);
    }
    await sleep(1500);

    // 3. Condition C: Iterative RAG (LangGraph)
    try {
      console.log(`  -> Running Condition C (Iterative RAG via LangGraph)...`);
      const resC = await runIterativeRAGNiche(niche);
      resultsIterative.push(resC);
      console.log(`     Pred: '${resC.predictedLabel}' (${resC.matchCategory}, conf: ${resC.confidence.toFixed(2)}, iter: ${resC.retrievalIterations})`);
    } catch (err: unknown) {
      console.error(`     Error Iterative: ${(err as Error).message}`);
    }
    await sleep(1500);

    console.log("");
  }

  // Compute aggregate summaries
  const summaryBaseline = computeBenchmarkSummary("Baseline", resultsBaseline);
  const summaryOneShot = computeBenchmarkSummary("OneShotRAG", resultsOneShot);
  const summaryIterative = computeBenchmarkSummary("IterativeRAG", resultsIterative);

  console.log("\n================================================================================");
  console.log("   BENCHMARK SUMMARY RESULTS");
  console.log("================================================================================");
  console.table([summaryBaseline, summaryOneShot, summaryIterative]);

  // Save results to docs/benchmark_results.json
  const docsDir = path.resolve(process.cwd(), "docs");
  if (!fs.existsSync(docsDir)) {
    fs.mkdirSync(docsDir, { recursive: true });
  }

  const outputPayload = {
    metadata: {
      dataset: "10x Visium Human DLPFC (151673)",
      date: new Date().toISOString(),
      nichesCount: totalNiches,
      methods: ["BANKSY", "CellCharter"]
    },
    summaries: {
      Baseline: summaryBaseline,
      OneShotRAG: summaryOneShot,
      IterativeRAG: summaryIterative
    },
    perNicheResults: {
      Baseline: resultsBaseline,
      OneShotRAG: resultsOneShot,
      IterativeRAG: resultsIterative
    }
  };

  const outputPath = path.join(docsDir, "benchmark_results.json");
  fs.writeFileSync(outputPath, JSON.stringify(outputPayload, null, 2));
  console.log(`\nDetailed benchmark results saved to: ${outputPath}`);

  return outputPayload;
}

runFullBenchmark().catch((err) => {
  console.error("Fatal benchmark error:", err);
  process.exit(1);
});
