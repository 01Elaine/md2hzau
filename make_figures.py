"""Generate example figures for example.md, saved to figures/"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

os.makedirs("figures", exist_ok=True)

# Okabe-Ito colorblind-safe palette (Nature Methods standard)
COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#56B4E9', '#CC79A7']
TEXT   = '#2D2D2D'
GRID   = '#E0E0E0'

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'text.color': TEXT,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'pdf.fonttype': 42,
})

# ── Fig 2-1: Model Architecture ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5.5))
ax.set_xlim(0, 13)
ax.set_ylim(0, 5.5)
ax.axis("off")
fig.patch.set_facecolor("white")

def draw_box(ax, x, y, w, h, fc, ec, lw=1.2, zorder=2, ls='-'):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.05",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder, linestyle=ls,
    )
    ax.add_patch(rect)

def sub_box(ax, x, y, w, h, label, fc, ec, fs=7.5):
    draw_box(ax, x, y, w, h, fc, ec, lw=0.8, zorder=4)
    ax.text(x+w/2, y+h/2, label, ha='center', va='center',
            fontsize=fs, color=TEXT, zorder=5)

arrow_kw = dict(arrowstyle="-|>", color=TEXT, lw=1.3, mutation_scale=11)

# ── Block 0: Input ──────────────────────────────────────────────────────────
BX, BY, BW, BH = 0.3, 1.2, 2.1, 2.8
draw_box(ax, BX, BY, BW, BH, '#EEF6FF', '#0072B2', lw=1.5)
ax.text(BX+BW/2, BY+BH-0.28, "Input", ha='center', va='center',
        fontsize=10, fontweight='bold', color='#0072B2', zorder=3)
# mini image icon (nested rectangles)
for k, (fc2, ec2) in enumerate([('#C8E0F4','#0072B2'),('#A0C8E8','#005A9E'),('#78B0DC','#004080')]):
    sub_box(ax, BX+0.18+k*0.15, BY+0.45+k*0.12, 1.4-k*0.3, 1.5-k*0.24, '', fc2, ec2)
ax.text(BX+BW/2, BY+0.35, "224×224×3", ha='center', va='center',
        fontsize=7.5, color='#0072B2', zorder=5)

# ── Block 1: Feature Extraction ─────────────────────────────────────────────
BX1, BY1, BW1, BH1 = 3.0, 0.6, 2.8, 3.8
draw_box(ax, BX1, BY1, BW1, BH1, '#FFF9EC', '#E69F00', lw=1.5)
ax.text(BX1+BW1/2, BY1+BH1-0.28, "Feature Extraction", ha='center', va='center',
        fontsize=10, fontweight='bold', color='#E69F00', zorder=3)
sub_label_y = [BY1+0.45, BY1+1.1, BY1+1.75, BY1+2.4]
sub_labels   = ["Conv 7×7, stride 2", "ResBlock ×3 (C=64)", "ResBlock ×4 (C=128)", "ResBlock ×6 (C=256)"]
sub_fcs      = ['#FFF3CC','#FFE8A0','#FFD970','#FFC840']
for sy, sl, sf in zip(sub_label_y, sub_labels, sub_fcs):
    sub_box(ax, BX1+0.18, sy, BW1-0.36, 0.5, sl, sf, '#E69F00')

# ── Block 2: Feature Fusion ──────────────────────────────────────────────────
BX2, BY2, BW2, BH2 = 6.5, 0.6, 2.8, 3.8
draw_box(ax, BX2, BY2, BW2, BH2, '#F0FAF5', '#009E73', lw=2.2)  # highlighted (novel)
ax.text(BX2+BW2/2, BY2+BH2-0.28, "Feature Fusion", ha='center', va='center',
        fontsize=10, fontweight='bold', color='#009E73', zorder=3)
ax.text(BX2+BW2/2, BY2+BH2-0.58, "* Novel Component", ha='center', va='center',
        fontsize=7, color='#009E73', style='italic', zorder=3)
sub_labels2 = ["Scale-1  (stride 4)", "Scale-2  (stride 8)", "Scale-3  (stride 16)"]
sub_fcs2    = ['#CCEEDF','#AADFC8','#88CEB1']
for k, (sl, sf) in enumerate(zip(sub_labels2, sub_fcs2)):
    sub_box(ax, BX2+0.18, BY2+0.45+k*0.7, BW2-0.36, 0.55, sl, sf, '#009E73')
# FPN arrow
ax.annotate("", xy=(BX2+BW2/2, BY2+0.45+2*0.7+0.27),
            xytext=(BX2+BW2/2, BY2+0.45+0.27),
            arrowprops=dict(arrowstyle="-|>", color='#009E73', lw=1.0,
                            mutation_scale=8, linestyle='dashed'))
ax.text(BX2+BW2-0.12, BY2+1.45, "FPN", ha='center', va='center',
        fontsize=6.5, color='#009E73', rotation=90, zorder=5)

# ── Block 3: Classifier ──────────────────────────────────────────────────────
BX3, BY3, BW3, BH3 = 10.0, 1.2, 2.5, 2.8
draw_box(ax, BX3, BY3, BW3, BH3, '#FFF2EE', '#D55E00', lw=1.5)
ax.text(BX3+BW3/2, BY3+BH3-0.28, "Classifier", ha='center', va='center',
        fontsize=10, fontweight='bold', color='#D55E00', zorder=3)
sub_labels3 = ["GAP", "FC  256→N", "Softmax"]
sub_fcs3    = ['#FFE5DA','#FFD0C0','#FFB8A0']
for k, (sl, sf) in enumerate(zip(sub_labels3, sub_fcs3)):
    sub_box(ax, BX3+0.2, BY3+0.38+k*0.7, BW3-0.4, 0.55, sl, sf, '#D55E00')

# ── Arrows between blocks ────────────────────────────────────────────────────
arrow_segs = [
    (BX+BW,   2.6,  BX1,       2.6,  "B×3×224×224"),
    (BX1+BW1, 2.5,  BX2,       2.5,  "B×256×28×28"),
    (BX2+BW2, 2.5,  BX3,       2.5,  "B×256×28×28"),
]
for x0, y0, x1, y1, label in arrow_segs:
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=arrow_kw, zorder=6)
    ax.text((x0+x1)/2, y0+0.18, label, ha='center', va='bottom',
            fontsize=7, color='#555555', zorder=6)

# ── Loss (top-right dashed) ───────────────────────────────────────────────────
ax.text(11.5, 5.05, "Cross-Entropy Loss", ha='center', va='center',
        fontsize=8, color='#888', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', fc='#F8F8F8', ec='#BBB', lw=0.8))
ax.annotate("", xy=(BX3+BW3*0.6, BY3+BH3),
            xytext=(11.5, 4.78),
            arrowprops=dict(arrowstyle="-|>", color='#AAA', lw=1.0,
                            mutation_scale=9, linestyle='dashed'))

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(6.5, 5.3, "Model Architecture", ha='center', va='center',
        fontsize=13, fontweight='bold', color=TEXT)

plt.savefig("figures/fig_architecture.png")
plt.close()
print("OK figures/fig_architecture.png")

# ── Fig 3-1: Accuracy Comparison on CIFAR-10 ───────────────────────────────
methods = ["VGGNet", "ResNet-50", "DenseNet", "ViT-B/16", "Ours"]
acc     = [91.4,     93.1,        93.8,        94.2,        95.6]
bar_colors = [COLORS[4]] * 4 + [COLORS[3]]

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(methods, acc, color=bar_colors, edgecolor="white",
              linewidth=0.8, width=0.55)

for bar, v in zip(bars, acc):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.1,
            f"{v:.1f}%", ha="center", va="bottom", fontsize=9)

ax.set_ylim(88, 97)
ax.set_ylabel("Accuracy (%)", fontsize=10)
ax.set_title("Accuracy Comparison on CIFAR-10", fontsize=11, fontweight="bold")
ax.yaxis.grid(True, color=GRID, linestyle="--", linewidth=0.6, alpha=0.8)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig_results.png")
plt.close()
print("OK figures/fig_results.png")
