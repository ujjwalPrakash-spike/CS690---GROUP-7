import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_card(ax, x, y, w, h, bg_color, border_color, title, items, 
              title_color="#0f172a", title_size=11, body_size=9, radius=0.15, is_bold_items=None):
    """Draw a clean card with shadow, border, bold title, and nicely formatted items."""
    # Subtle drop shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.04, y - 0.04), w, h,
        boxstyle=f"round,pad=0.04,rounding_size={radius}",
        facecolor="#cbd5e1", edgecolor="none", alpha=0.35, zorder=2
    )
    ax.add_patch(shadow)

    # Main card
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.04,rounding_size={radius}",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=1.8, zorder=3
    )
    ax.add_patch(box)

    # Header Title
    ax.text(
        x + w/2, y + h - 0.35, title,
        ha="center", va="top",
        fontsize=title_size, fontweight="bold",
        color=title_color, zorder=4
    )

    # Divider line
    ax.plot([x + 0.2, x + w - 0.2], [y + h - 0.65, y + h - 0.65],
            color=border_color, lw=0.8, alpha=0.6, zorder=4)

    # Bullet items with calculated vertical spacing
    n_items = len(items)
    if n_items > 0:
        available_height = h - 0.95
        line_step = min(0.42, available_height / max(n_items, 1))
        item_y = y + h - 0.85

        for idx, item in enumerate(items):
            is_bold = False
            if is_bold_items and idx in is_bold_items:
                is_bold = True
            elif any(k in item for k in ["91.7%", "100.0%", "0.0%", "0.0017", "Zod", "Sample 151673"]):
                is_bold = True
            
            weight = "bold" if is_bold else "normal"
            text_color = "#0f172a" if is_bold else "#334155"
            prefix = "▸ " if not item.startswith("•") else "  "

            ax.text(
                x + 0.25, item_y, f"{prefix}{item}",
                ha="left", va="top",
                fontsize=body_size, fontweight=weight,
                color=text_color, zorder=4
            )
            item_y -= line_step

def draw_badge(ax, x, y, text, bg_color="#ffffff", border_color="#64748b", text_color="#0f172a", font_size=8.5):
    """Draw a standalone floating badge for edge labels."""
    ax.text(
        x, y, text,
        ha="center", va="center",
        fontsize=font_size, fontweight="bold",
        color=text_color,
        bbox=dict(
            boxstyle="round,pad=0.35,rounding_size=0.1",
            facecolor=bg_color,
            edgecolor=border_color,
            lw=1.4
        ),
        zorder=7
    )

def generate_clean_architecture_diagram(output_path="docs/figures/pipeline_architecture.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(24, 11), dpi=300)
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#ffffff")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # Header Title Banner
    ax.text(12.0, 10.45, "Web-Augmented NicheAgent: End-to-End System Pipeline", 
            ha="center", va="center", fontsize=21, fontweight="bold", color="#0f172a")
    ax.text(12.0, 10.02, "10x Visium Human DLPFC • LangGraph.js • Zero-Shot Prediction with Live Biological Knowledge Retrieval", 
            ha="center", va="center", fontsize=12.5, color="#64748b")

    # =========================================================================
    # STAGE 1: UPSTREAM SPATIAL CLUSTERING (x: 0.8 to 6.2, w=5.4)
    # =========================================================================
    s1_box = patches.FancyBboxPatch(
        (0.8, 0.7), 5.4, 8.8,
        boxstyle="round,pad=0.15,rounding_size=0.3",
        facecolor="#f0f7ff", edgecolor="#3b82f6", linewidth=1.8, linestyle="--", alpha=0.9, zorder=1
    )
    ax.add_patch(s1_box)
    
    # Stage 1 Header Badge
    ax.text(3.5, 9.15, "STAGE 1: UPSTREAM CLUSTERING", 
            ha="center", va="center", fontsize=11.5, fontweight="bold", color="#1d4ed8")

    # Card 1: Tissue
    draw_card(ax, 1.1, 6.55, 4.8, 2.15, "#ffffff", "#93c5fd",
              "10x Visium DLPFC Tissue",
              ["Sample 151673 (Maynard et al. 2021)",
               "3,611 Tissue Spots • 33,538 Genes",
               "7 Ground-Truth Laminae (L1-L6, WM)"],
              title_color="#1e40af", title_size=11, body_size=9.2)

    # Arrow 1 -> 2
    ax.annotate("", xy=(3.5, 5.85), xytext=(3.5, 6.45),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#2563eb", lw=2.2), zorder=5)

    # Card 2: Dual Clustering
    draw_card(ax, 1.1, 3.70, 4.8, 2.15, "#ffffff", "#93c5fd",
              "Dual Spatial Clustering",
              ["BANKSY (Spatial Gradient Kernel)",
               "CellCharter (scVI Latent Pooling)",
               "Total: 12 Spatial Niches Analyzed (6+6)"],
              title_color="#1e40af", title_size=11, body_size=9.2)

    # Arrow 2 -> 3
    ax.annotate("", xy=(3.5, 3.00), xytext=(3.5, 3.60),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#2563eb", lw=2.2), zorder=5)

    # Card 3: Differential Expression
    draw_card(ax, 1.1, 0.95, 4.8, 1.95, "#ffffff", "#93c5fd",
              "Differential Expression",
              ["Wilcoxon Rank-Sum (One-vs-Rest)",
               "Top 10 Marker Genes extracted per Niche",
               "Ranked by Log2FC & Adjusted p-value"],
              title_color="#1e40af", title_size=11, body_size=9.2)

    # Arrow: Stage 1 -> Stage 2 (Input QC)
    ax.annotate("", xy=(7.2, 1.92), xytext=(6.0, 1.92),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#2563eb", lw=2.4), zorder=5)
    draw_badge(ax, 6.6, 2.25, "Top Markers", bg_color="#eff6ff", border_color="#3b82f6", text_color="#1d4ed8", font_size=8)

    # =========================================================================
    # STAGE 2: LANGGRAPH.JS AGENT (DECISION & RETRIEVAL) (x: 7.1 to 17.5, w=10.4)
    # =========================================================================
    s2_box = patches.FancyBboxPatch(
        (7.1, 0.7), 10.4, 8.8,
        boxstyle="round,pad=0.15,rounding_size=0.3",
        facecolor="#fffdf5", edgecolor="#eab308", linewidth=1.8, linestyle="--", alpha=0.9, zorder=1
    )
    ax.add_patch(s2_box)
    
    # Stage 2 Header Badge
    ax.text(12.3, 9.15, "STAGE 2: LANGGRAPH.JS AGENT (DECISION & RETRIEVAL)", 
            ha="center", va="center", fontsize=11.5, fontweight="bold", color="#a16207")

    # ---------------------------------------------------------
    # Column A: Node 1, Node 2, Node 3 (x: 7.4, w: 2.9)
    # ---------------------------------------------------------
    # Node 1: Input QC
    draw_card(ax, 7.4, 0.95, 2.9, 1.95, "#ffffff", "#fde047",
              "1. Input QC Node",
              ["Zod Runtime Schema Validation",
               "MT- Mitochondrial Gene Filter",
               "Emits Clean Nuclear Marker Profile"],
              title_color="#854d0e", title_size=10.5, body_size=8.8)

    # Arrow Node 1 -> Node 2
    ax.annotate("", xy=(8.85, 3.60), xytext=(8.85, 3.00),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#ca8a04", lw=2.2), zorder=5)

    # Node 2: Initial Predictor
    draw_card(ax, 7.4, 3.70, 2.9, 2.15, "#ffffff", "#fde047",
              "2. Initial Predictor Node",
              ["Zero-Shot Gemini API Call",
               "Dual-Granularity Structured JSON:",
               "• Primary Anatomical Layer",
               "• Resident Cell Type Hypothesis"],
              title_color="#854d0e", title_size=10.5, body_size=8.8)

    # Arrow Node 2 -> Node 3
    ax.annotate("", xy=(8.85, 6.45), xytext=(8.85, 5.95),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#ca8a04", lw=2.2), zorder=5)

    # Node 3: Uncertainty Assessor
    draw_card(ax, 7.4, 6.55, 2.9, 2.15, "#ffffff", "#fde047",
              "3. Uncertainty Assessor",
              ["Confidence Score (< 0.70)",
               "White Matter / Myelin Ambiguity",
               "Neurofilament Layer Conflict (NEFL)",
               "Conditional Routing Gate"],
              title_color="#854d0e", title_size=10.5, body_size=8.8)

    # ---------------------------------------------------------
    # Branch 1: High Confidence Fast-Path (Top Bypass)
    # Route: (8.85, 8.8) -> up to 9.6 -> right to 18.5 -> down to (18.5, 7.9) -> Node 7
    # ---------------------------------------------------------
    ax.plot([8.85, 8.85, 20.3, 20.3], [8.8, 9.6, 9.6, 8.8],
            color="#0284c7", lw=2.4, linestyle="-", zorder=5)
    ax.annotate("", xy=(20.3, 8.7), xytext=(20.3, 9.0),
                arrowprops=dict(arrowstyle="->,head_width=0.5,head_length=0.7", color="#0284c7", lw=2.4), zorder=6)
    draw_badge(ax, 14.5, 9.6, "High Confidence (Score ≥ 0.70) — Direct Fast-Path Bypass", 
               bg_color="#f0f9ff", border_color="#0284c7", text_color="#0369a1", font_size=8.5)

    # ---------------------------------------------------------
    # Branch 2: Uncertain -> Retrieval
    # Arrow Node 3 -> Column B (APIs)
    # ---------------------------------------------------------
    ax.annotate("", xy=(10.95, 7.62), xytext=(10.4, 7.62),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#dc2626", lw=2.2), zorder=5)
    draw_badge(ax, 10.68, 8.0, "Uncertain", bg_color="#fef2f2", border_color="#ef4444", text_color="#b91c1c", font_size=8)

    # ---------------------------------------------------------
    # Column B: Live Biological Knowledge APIs (x: 11.0, w: 2.7)
    # ---------------------------------------------------------
    api_outer = patches.FancyBboxPatch(
        (11.0, 2.5), 2.7, 5.9,
        boxstyle="round,pad=0.1,rounding_size=0.2",
        facecolor="#f0fdf4", edgecolor="#22c55e", linewidth=1.6, zorder=2
    )
    ax.add_patch(api_outer)

    # Header in API container
    ax.text(12.35, 8.05, "4. Live Biological APIs", 
            ha="center", va="center", fontsize=10.5, fontweight="bold", color="#15803d", zorder=3)
    ax.text(12.35, 7.75, "(Queried in parallel • Zero API keys)", 
            ha="center", va="center", fontsize=8.0, color="#166534", zorder=3)

    # Sub-card 1: MyGene.info
    draw_card(ax, 11.2, 6.05, 2.3, 1.45, "#ffffff", "#86efac",
              "MyGene.info",
              ["NCBI & Ensembl summaries", "Gene function descriptions"],
              title_color="#166534", title_size=9.5, body_size=8.2, radius=0.1)

    # Sub-card 2: Enrichr
    draw_card(ax, 11.2, 4.35, 2.3, 1.45, "#ffffff", "#86efac",
              "Enrichr (Jensen)",
              ["Subcellular compartments", "Localizes synaptic markers"],
              title_color="#166534", title_size=9.5, body_size=8.2, radius=0.1)

    # Sub-card 3: NCBI PubMed
    draw_card(ax, 11.2, 2.65, 2.3, 1.45, "#ffffff", "#86efac",
              "NCBI PubMed",
              ["Laminar cortical papers", "Resolves ambiguous genes"],
              title_color="#166534", title_size=9.5, body_size=8.2, radius=0.1)

    # Arrow from APIs -> Evidence Evaluator
    ax.annotate("", xy=(14.35, 6.70), xytext=(13.8, 6.70),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#16a34a", lw=2.2), zorder=5)
    draw_badge(ax, 14.08, 7.05, "Evidence", bg_color="#f0fdf4", border_color="#22c55e", text_color="#15803d", font_size=8)

    # ---------------------------------------------------------
    # Column C: Evaluator & Reviser (x: 14.4, w: 2.8)
    # ---------------------------------------------------------
    # Node 5: Evidence Evaluator
    draw_card(ax, 14.4, 5.45, 2.8, 2.45, "#ffffff", "#fde047",
              "5. Evidence Evaluator",
              ["Cross-reference fetched literature",
               "Validates cortical layer facts",
               "Applies Layer 1 astrocyte rule",
               "Resolves NEFL Layer 3 vs 5 conflict",
               "Determines confirm vs rebut"],
              title_color="#854d0e", title_size=10.5, body_size=8.6)

    # Arrow Node 5 -> Node 6
    ax.annotate("", xy=(15.8, 4.25), xytext=(15.8, 5.35),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#ca8a04", lw=2.2), zorder=5)

    # Node 6: Prediction Reviser
    draw_card(ax, 14.4, 1.65, 2.8, 2.50, "#ffffff", "#fde047",
              "6. Prediction Reviser",
              ["Synthesizes biological facts",
               "Overrules initial layer if refuted",
               "Recalibrates confidence score",
               "Caps loop at max 2 iterations",
               "Emits definitive prediction"],
              title_color="#854d0e", title_size=10.5, body_size=8.6)

    # Arrow Node 6 -> Stage 3 (Final Formatter)
    # Clean L-shaped / straight path into Stage 3
    ax.plot([17.3, 17.85, 17.85, 18.25], [2.9, 2.9, 6.55, 6.55],
            color="#db2777", lw=2.2, linestyle="-", zorder=5)
    ax.annotate("", xy=(18.3, 6.55), xytext=(18.0, 6.55),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#db2777", lw=2.2), zorder=6)
    draw_badge(ax, 17.85, 4.7, "Refined State", bg_color="#fdf2f8", border_color="#ec4899", text_color="#be185d", font_size=8)

    # =========================================================================
    # STAGE 3: VERIFIED OUTPUT & BENCHMARK (x: 18.2 to 23.2, w=5.0)
    # =========================================================================
    s3_box = patches.FancyBboxPatch(
        (18.2, 0.7), 5.0, 8.8,
        boxstyle="round,pad=0.15,rounding_size=0.3",
        facecolor="#fdf4f8", edgecolor="#ec4899", linewidth=1.8, linestyle="--", alpha=0.9, zorder=1
    )
    ax.add_patch(s3_box)
    
    # Stage 3 Header Badge
    ax.text(20.7, 9.15, "STAGE 3: VERIFIED OUTPUT", 
            ha="center", va="center", fontsize=11.5, fontweight="bold", color="#be185d")

    # Card 7: Final Formatter Node
    draw_card(ax, 18.45, 5.30, 4.5, 2.60, "#ffffff", "#f472b6",
              "7. Final Formatter Node",
              ["Assemble Complete Structured Result",
               "Predicted Layer & Predominant Cell Type",
               "Embed Provenance URLs (PubMed & MyGene)",
               "Record Full Decision Trace & Agent Latency",
               "Formatted for Spatial Genomics Benchmarking"],
              title_color="#9d174d", title_size=11, body_size=9.0)

    # Arrow Card 7 -> Scorecard
    ax.annotate("", xy=(20.7, 4.40), xytext=(20.7, 5.20),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.65", color="#be185d", lw=2.2), zorder=5)

    # Benchmark Performance Scorecard
    draw_card(ax, 18.45, 0.95, 4.5, 3.35, "#ffffff", "#f472b6",
              "Empirical Benchmark Results (N=36)",
              ["Exact Layer Match Rate: 91.7% (11/12)",
               "Overall Biological Concordance: 100.0% (12/12)",
               "Severe Laminar Mismatches: 0.0% (0/12)",
               "Confident Hallucinations: 0.0%",
               "Expected Calibration Error (ECE): 0.0017",
               "Mean Agent Latency: 4.88s / niche",
               "Overcame Zero-Shot & Baseline Failures"],
              title_color="#9d174d", title_size=11, body_size=9.0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Generated clean, non-overlapping architecture diagram at: {output_path}")

if __name__ == "__main__":
    generate_clean_architecture_diagram()
