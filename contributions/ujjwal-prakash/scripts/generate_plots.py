import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def generate_benchmark_figures(json_path="docs/benchmark_results.json", output_dir="docs/figures"):
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(json_path):
        print(f"Results file {json_path} does not exist yet.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    summaries = data["summaries"]
    conditions = ["Baseline", "OneShotRAG", "IterativeRAG"]
    labels = ["Baseline (Gemini)", "One-Shot RAG", "Iterative RAG (LangGraph)"]

    exact_rates = [summaries[c]["exactMatchRate"] * 100 for c in conditions]
    partial_rates = [summaries[c]["partialMatchRate"] * 100 for c in conditions]
    mismatch_rates = [summaries[c]["mismatchRate"] * 100 for c in conditions]
    conf_wrong_rates = [summaries[c]["confidentlyWrongRate"] * 100 for c in conditions]
    mean_conf = [summaries[c]["meanConfidence"] * 100 for c in conditions]
    latencies = [summaries[c]["meanLatencyMs"] / 1000.0 for c in conditions]

    # --- FIGURE 1: Accuracy Breakdown (Exact, Partial, Mismatch) ---
    plt.figure(figsize=(9, 5))
    bar_width = 0.55
    x = np.arange(len(conditions))

    p1 = plt.bar(x, exact_rates, width=bar_width, label="Exact Match", color="#2ca02c")
    p2 = plt.bar(x, partial_rates, width=bar_width, bottom=exact_rates, label="Partial Match", color="#ff7f0e")
    bottom_mismatch = [e + p for e, p in zip(exact_rates, partial_rates)]
    p3 = plt.bar(x, mismatch_rates, width=bar_width, bottom=bottom_mismatch, label="Mismatch", color="#d62728")

    plt.ylabel("Proportion of Niches (%)", fontsize=12)
    plt.title("Spatial Niche Annotation Accuracy on 10x Visium DLPFC (N=12 Niches)", fontsize=14, fontweight="bold")
    plt.xticks(x, labels, fontsize=11)
    plt.ylim(0, 105)
    plt.legend(loc="upper right", frameon=True)
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for i in range(len(conditions)):
        plt.text(i, exact_rates[i] / 2 if exact_rates[i] > 5 else exact_rates[i] + 2, f"{exact_rates[i]:.1f}%", ha="center", va="center", color="white" if exact_rates[i] > 15 else "black", fontweight="bold")

    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "benchmark_accuracy_breakdown.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Saved: {fig1_path}")

    # --- FIGURE 2: Confident Hallucinations & Calibration ---
    plt.figure(figsize=(9, 5))
    x = np.arange(len(conditions))
    width = 0.35

    plt.bar(x - width/2, conf_wrong_rates, width=width, label="Confidently Wrong Rate (%)", color="#d62728")
    plt.bar(x + width/2, mean_conf, width=width, label="Mean Confidence (%)", color="#1f77b4")

    plt.ylabel("Percentage (%)", fontsize=12)
    plt.title("Confidence Calibration vs. Confident Hallucinations", fontsize=14, fontweight="bold")
    plt.xticks(x, labels, fontsize=11)
    plt.ylim(0, 105)
    plt.legend(loc="upper right", frameon=True)
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for i in range(len(conditions)):
        plt.text(i - width/2, conf_wrong_rates[i] + 2, f"{conf_wrong_rates[i]:.1f}%", ha="center", fontweight="bold")
        plt.text(i + width/2, mean_conf[i] + 2, f"{mean_conf[i]:.1f}%", ha="center", fontweight="bold")

    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "benchmark_hallucination_calibration.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Saved: {fig2_path}")

    # --- FIGURE 3: Latency & Computational Overhead ---
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(labels, latencies, color=["#7f7f7f", "#17becf", "#9467bd"], width=0.5)
    plt.ylabel("Mean Latency per Niche (seconds)", fontsize=12)
    plt.title("Execution Latency across Experimental Paradigms", fontsize=14, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f}s", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "benchmark_latency.png")
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"Saved: {fig3_path}")

if __name__ == "__main__":
    generate_benchmark_figures()
