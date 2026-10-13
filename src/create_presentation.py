
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
import textwrap

ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "plots"
RESULTS = ROOT / "results"
OUT = ROOT / "presentation.pdf"

W, H = 960, 540  # 16:9 landscape
BG = HexColor("#0B1020")
PANEL = HexColor("#151D33")
ACCENT = HexColor("#69E2D0")
BLUE = HexColor("#8CA8FF")
MUTED = HexColor("#B7C2D8")
TEXT = HexColor("#F4F7FF")

c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle("Quantum Portfolio Optimization Using QAOA")
c.setAuthor("Qiskit Fall Fest 2026 - Track 2")

def background(section, page):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(42, H - 43, 34, 4, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(86, H - 45, section.upper())
    c.drawRightString(W - 42, 23, f"QAOA PORTFOLIO STUDY  •  {page}/8")
    c.setStrokeColor(HexColor("#29334D"))
    c.line(42, 39, W - 42, 39)

def title(text, subtitle=None):
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 25)
    c.drawString(42, H - 91, text)
    if subtitle:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 11)
        c.drawString(43, H - 114, subtitle)

def paragraph(text, x, y, width=420, size=12, leading=18,
              color=TEXT, font="Helvetica"):
    c.setFillColor(color)
    c.setFont(font, size)
    max_chars = max(15, int(width / (size * 0.52)))
    for para in text.split("\n"):
        lines = textwrap.wrap(para, width=max_chars) or [""]
        for line in lines:
            c.drawString(x, y, line)
            y -= leading
        y -= 4
    return y

def bullet_list(items, x, y, width=410, size=12, leading=18):
    for item in items:
        c.setFillColor(ACCENT)
        c.circle(x + 4, y + 3, 3, fill=1, stroke=0)
        y = paragraph(item, x + 17, y, width - 17, size, leading)
        y -= 7
    return y

def card(x, y, w, h, heading, value, note=""):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 12, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(x + 16, y + h - 25, heading)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 23)
    c.drawString(x + 16, y + h - 56, value)
    if note:
        paragraph(note, x + 16, y + 19, w - 32, 9, 12, MUTED)

def add_image(path, x, y, w, h):
    if not path.exists():
        paragraph(f"Plot not found: {path.name}", x, y + h - 20,
                  w, 10, 13, MUTED)
        return
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2,
                dw, dh, preserveAspectRatio=True, mask="auto")

def new_page(section, page):
    c.showPage()
    background(section, page)

# ------------------------------------------------------------
# 1. Title
# ------------------------------------------------------------
background("Track 2 • Quantum Optimization", 1)
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 11)
c.drawString(54, 430, "QISKIT FALL FEST 2026")

c.setFillColor(TEXT)
c.setFont("Helvetica-Bold", 34)
c.drawString(54, 366, "Quantum Portfolio")
c.drawString(54, 322, "Optimization with QAOA")

paragraph(
    "A six-stock statevector study with an exact classical baseline, "
    "parameter sweeps, and constraint-aware classical post-processing.",
    56, 276, 480, 15, 22, MUTED
)

card(590, 302, 145, 102, "STOCKS", "6", "Synthetic instance")
card(752, 302, 154, 102, "PORTFOLIO SIZE", "3", "Exact-cardinality")
card(590, 176, 145, 102, "QAOA DEPTHS", "1–4", "Compared")
card(752, 176, 154, 102, "NEW FEATURE", "Q-Repair", "Classical recovery")

paragraph("Research prototype • Reproducible local experiments",
          56, 105, 520, 11, 16, MUTED)
c.showPage()

# ------------------------------------------------------------
# 2. Problem
# ------------------------------------------------------------
background("01 • Problem formulation", 2)
title("Portfolio selection as binary optimization",
      "Balance risk and expected return while selecting exactly K stocks.")

c.setFillColor(PANEL)
c.roundRect(45, 228, 540, 155, 12, fill=1, stroke=0)
paragraph("Minimize the penalized objective:", 65, 350, 490, 12, 17, MUTED)
c.setFillColor(TEXT)
c.setFont("Helvetica", 15)
c.drawString(66, 310, "C(x) = q xᵀΣx − μᵀx + λ(Σxᵢ − K)²")
paragraph("xᵢ ∈ {0,1}  •  n = 6  •  K = 3  •  q = 0.5",
          66, 278, 490, 11, 17, ACCENT)

bullet_list([
    "Binary decision: select or do not select each stock.",
    "Risk term: quadratic form using a positive semidefinite matrix.",
    "Return term: rewards higher expected returns.",
    "Penalty: discourages portfolios with the wrong number of stocks."
], 625, 354, 280, 11, 17)

paragraph(
    "Data is synthetic and generated deterministically with NumPy seed 2026. "
    "It is a benchmark instance, not a claim about real market performance.",
    55, 160, 830, 12, 18, MUTED
)
c.showPage()

# ------------------------------------------------------------
# 3. Classical baseline
# ------------------------------------------------------------
background("02 • Classical baseline", 3)
title("Establish the reference optimum",
      "Exhaustive search checks every portfolio satisfying the constraint.")

card(52, 295, 195, 105, "ALL BITSTRINGS", "64", "2⁶ candidates")
card(267, 295, 195, 105, "FEASIBLE SET", "20", "Choose 3 of 6")
card(482, 295, 195, 105, "BEST COST", "−0.503015", "Original objective")
card(697, 295, 210, 105, "OPTIMAL STOCKS", "2, 3, 6", "One-based indices")

paragraph("Optimal bitstring: 011001", 58, 243, 420, 14, 20, ACCENT)
bullet_list([
    "The exact feasible optimum is the reference for QAOA evaluation.",
    "Classical enumeration is inexpensive at six stocks.",
    "For twelve stocks with six selections, there are 924 feasible portfolios."
], 60, 200, 790, 12, 18)

paragraph(
    "The 12-stock experiment is a separate classical baseline. "
    "No completed 12-stock QAOA result is claimed.",
    60, 105, 800, 11, 17, MUTED
)
c.showPage()

# ------------------------------------------------------------
# 4. QAOA methodology
# ------------------------------------------------------------
background("03 • Methodology", 4)
title("Alternating cost and mixer operations",
      "Statevector QAOA experiments with p = 1, 2, 3, and 4.")

steps = [
    ("01", "Initialize", "Uniform superposition over 64 bitstrings."),
    ("02", "Cost phase", "Apply exp(−iγC(x)) to each basis-state amplitude."),
    ("03", "Mixer", "Apply RX(2β) to each of the six qubits."),
    ("04", "Optimize", "Use COBYLA to minimize expected penalized cost."),
]
for i, (num, head, desc) in enumerate(steps):
    y = 356 - i * 78
    c.setFillColor(PANEL)
    c.roundRect(55, y - 30, 850, 60, 10, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(75, y - 4, num)
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(125, y + 4, head)
    paragraph(desc, 285, y + 4, 570, 10, 14, MUTED)

paragraph(
    "Implementation note: the current experiment applies cost phases and "
    "single-qubit mixers directly to a statevector. It is not evidence of "
    "hardware execution or GPU acceleration.",
    58, 75, 820, 10, 15, MUTED
)
c.showPage()

# ------------------------------------------------------------
# 5. Depth sweep
# ------------------------------------------------------------
background("04 • Depth experiment", 5)
title("Depth changes multiple performance metrics",
      "Observed results from the finite-budget QAOA depth sweep.")

add_image(PLOTS / "qaoa_probabilities.png", 48, 100, 420, 300)
add_image(PLOTS / "qaoa_expected_cost.png", 492, 100, 420, 300)

c.setFillColor(PANEL)
c.roundRect(50, 53, 860, 36, 8, fill=1, stroke=0)
paragraph(
    "p=3: feasibility 92.69%, optimum probability 5.03%. "
    "p=4: lowest observed expected cost (−0.213192). "
    "All p=2–4 runs reached the 100-evaluation budget.",
    64, 75, 830, 9, 12, TEXT
)
c.showPage()

# ------------------------------------------------------------
# 6. Penalty sweep
# ------------------------------------------------------------
background("05 • Penalty experiment", 6)
title("Penalty strength is a trade-off",
      "Feasibility and exact-optimum probability need not peak together.")

add_image(PLOTS / "qaoa_penalty_sweep.png", 70, 120, 530, 315)

card(635, 315, 270, 90, "HIGHEST FEASIBILITY", "67.10%", "λ = 5 in tested sweep")
card(635, 205, 270, 90, "HIGHEST OPTIMUM MASS", "3.68%", "λ = 1 in tested sweep")

paragraph(
    "Some optimizer runs returned success=False. The finite search budget "
    "and non-monotonic results limit conclusions; these are observed runs, "
    "not globally optimized penalty settings.",
    78, 90, 800, 11, 17, MUTED
)
c.showPage()

# ------------------------------------------------------------
# 7. Q-Repair and stability
# ------------------------------------------------------------
background("06 • Additional contribution", 7)
title("Q-Repair: constraint-aware post-processing",
      "Map each sampled bitstring to a nearby feasible portfolio.")

add_image(PLOTS / "q_repair_comparison.png", 48, 128, 490, 275)

card(580, 315, 320, 88, "RAW OPTIMUM PROBABILITY", "5.03%", "Selected p=3 run")
card(580, 207, 320, 88, "AFTER REPAIR", "8.81%", "Mapped probability mass")

bullet_list([
    "Repair changes the fewest bits needed to reach exactly three stocks.",
    "Ties are resolved by the original portfolio objective.",
    "All eight optimizer starts reached the 100-evaluation limit.",
    "Classical repair is not quantum advantage."
], 70, 115, 820, 10, 14)

c.showPage()

# ------------------------------------------------------------
# 8. Conclusions and limitations
# ------------------------------------------------------------
background("07 • Conclusion", 8)
title("What we learned",
      "A reproducible optimization study—not a claim of quantum advantage.")

bullet_list([
    "Exhaustive search establishes the six-stock optimum: stocks 2, 3, 6.",
    "QAOA depth and penalty settings affect feasibility and solution quality differently.",
    "Q-Repair increased mapped optimum probability mass from 5.03% to 8.81% in the selected run.",
    "Optimizer initialization sensitivity remains significant under the current budget.",
    "The 12-stock result is classical; no larger QAOA success is claimed."
], 60, 365, 810, 12, 18)

c.setFillColor(PANEL)
c.roundRect(55, 75, 850, 105, 12, fill=1, stroke=0)
paragraph("Next steps", 75, 153, 180, 12, 17, ACCENT, "Helvetica-Bold")
paragraph(
    "Improve optimizer convergence, test repeated seeds, compare with a "
    "gate-level Qiskit circuit, and evaluate on historical financial data.",
    75, 126, 790, 11, 17, TEXT
)

paragraph(
    "Reproducibility: Python • NumPy • SciPy • Qiskit • statevector simulation",
    58, 54, 820, 9, 13, MUTED
)

c.save()
print(f"Presentation saved: {OUT}")
print("Pages: 8")
