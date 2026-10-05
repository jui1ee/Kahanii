import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DIAGRAMS_DIR = r"c:\Users\Durgesh Shukla\Kahanii\diagrams"
DOCS_FIG_DIR = r"c:\Users\Durgesh Shukla\Kahanii\docs\figures"
DOCS_DIR = r"c:\Users\Durgesh Shukla\Kahanii\docs"

os.makedirs(DIAGRAMS_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. PLAYBACK ENGINE ARCHITECTURE (Diagram 1)
# ---------------------------------------------------------
def create_playback_engine_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F8F9FA')

    # Hide axes
    ax.axis('off')
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)

    # Title
    ax.text(7, 7.5, "Playback Engine Architecture", fontsize=18, fontweight='bold', ha='center', va='center', color='#2D3436')
    ax.text(7, 7.1, "Kahanii Sign Language & Audio Narration Synchronization Engine", fontsize=11, fontstyle='italic', ha='center', va='center', color='#636E72')

    # Color Palette
    c_blue = '#4A90E2'
    c_purple = '#8E44AD'
    c_green = '#2ECC71'
    c_orange = '#E67E22'
    c_dark = '#2C3E50'

    # Box 1: Story Tokens
    b1 = patches.FancyBboxPatch((0.5, 4.5), 3.2, 1.8, boxstyle="round,pad=0.2", fc='#EBF5FB', ec=c_blue, lw=2)
    ax.add_patch(b1)
    ax.text(2.1, 5.9, "1. Input Token List", fontsize=12, fontweight='bold', color=c_blue, ha='center')
    ax.text(2.1, 5.3, "Ordered List[StoryToken]\n• display_word\n• lemma\n• sign_video / is_fs", fontsize=9, color='#34495E', ha='center')

    # Arrow 1 -> 2
    ax.annotate("", xy=(4.2, 5.4), xytext=(3.9, 5.4), arrowprops=dict(arrowstyle="->", lw=2, color=c_dark))

    # Box 2: Spoken Unit Expansion
    b2 = patches.FancyBboxPatch((4.4, 4.5), 3.8, 1.8, boxstyle="round,pad=0.2", fc='#F5EEF8', ec=c_purple, lw=2)
    ax.add_patch(b2)
    ax.text(6.3, 5.9, "2. Spoken-Unit Expansion", fontsize=12, fontweight='bold', color=c_purple, ha='center')
    ax.text(6.3, 5.2, "spokenUnits memo array:\n• Sign-Video Token = 1 unit ('horse')\n• Fingerspelled Token = N units ('C','A','T')", fontsize=9, color='#34495E', ha='center')

    # Arrow 2 -> Split branches
    ax.annotate("", xy=(8.7, 5.9), xytext=(8.4, 5.4), arrowprops=dict(arrowstyle="->", lw=2, color=c_dark))
    ax.annotate("", xy=(8.7, 4.9), xytext=(8.4, 5.4), arrowprops=dict(arrowstyle="->", lw=2, color=c_dark))

    # Box 3A: Audio Narration (Web Speech API)
    b3a = patches.FancyBboxPatch((8.9, 5.4), 4.6, 1.3, boxstyle="round,pad=0.2", fc='#E8F8F5', ec=c_green, lw=2)
    ax.add_patch(b3a)
    ax.text(11.2, 6.3, "3A. Audio Narration Channel", fontsize=11, fontweight='bold', color=c_green, ha='center')
    ax.text(11.2, 5.7, "SpeechSynthesisUtterance(unit.surface)\nRate=0.9, Pitch=1.05 | Non-blocking Audio", fontsize=8.5, color='#27AE60', ha='center')

    # Box 3B: setTimeout Loop & UI Engine
    b3b = patches.FancyBboxPatch((8.9, 3.4), 4.6, 1.6, boxstyle="round,pad=0.2", fc='#FEF9E7', ec=c_orange, lw=2)
    ax.add_patch(b3b)
    ax.text(11.2, 4.6, "3B. Timer Loop & Video Engine", fontsize=11, fontweight='bold', color=c_orange, ha='center')
    ax.text(11.2, 3.9, "setTimeout(UNIT_DURATION_MS = 1350ms)\n1. Update activeIdx / activeLetter\n2. Shift active CSS highlight\n3. Swap & reload <video> src clip", fontsize=8.5, color='#D35400', ha='center')

    # Merge Arrow to Post-Roll
    ax.annotate("", xy=(7.0, 2.5), xytext=(11.2, 3.2), arrowprops=dict(arrowstyle="->", lw=2, color=c_dark, connectionstyle="angle,angleA=0,angleB=-90,rad=10"))

    # Box 4: Post-Roll Hold & Cleanup
    b4 = patches.FancyBboxPatch((4.5, 1.0), 5.0, 1.4, boxstyle="round,pad=0.2", fc='#EBEDEF', ec='#7F8C8D', lw=2)
    ax.add_patch(b4)
    ax.text(7.0, 2.0, "4. Post-Roll Hold & End State", fontsize=12, fontweight='bold', color='#2C3E50', ha='center')
    ax.text(7.0, 1.4, "POST_ROLL_MS = 700 ms hold on final gesture\nReset active state, clear timer, stop video loop", fontsize=9, color='#7F8C8D', ha='center')

    out_path = os.path.join(DIAGRAMS_DIR, "01_playback_engine_architecture.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print("Created Diagram 1:", out_path)

# ---------------------------------------------------------
# 2. COMBINED EDA DATASET PANELS (Diagram 2)
# ---------------------------------------------------------
def create_dataset_combined_diagram():
    img1_path = os.path.join(DOCS_FIG_DIR, "eda_01_class_balance.png")
    img2_path = os.path.join(DOCS_FIG_DIR, "eda_02_splits.png")

    if not (os.path.exists(img1_path) and os.path.exists(img2_path)):
        print("Warning: EDA panel source images missing!")
        return

    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    # Resize img2 height to match img1 height while maintaining aspect ratio
    h1 = img1.height
    w2_new = int(img2.width * (h1 / img2.height))
    img2_resized = img2.resize((w2_new, h1), Image.Resampling.LANCZOS)

    # Combined canvas width
    padding = 40
    title_height = 80
    combined_width = img1.width + img2_resized.width + (padding * 3)
    combined_height = h1 + title_height + (padding * 2)

    combined = Image.new("RGB", (combined_width, combined_height), "#FFFFFF")
    draw = ImageDraw.Draw(combined)

    # Paste panel images
    combined.paste(img1, (padding, title_height + padding))
    combined.paste(img2_resized, (padding * 2 + img1.width, title_height + padding))

    # Add Panel Titles
    # Panel (a) label
    draw.text((padding + 20, 20), "(a) Class Distribution Across 35 Hemg Classes", fill="#2D3436")
    # Panel (b) label
    draw.text((padding * 2 + img1.width + 20, 20), "(b) Dataset Splitting (80% Train, 10% Val, 10% Test)", fill="#2D3436")

    out_path = os.path.join(DIAGRAMS_DIR, "02_hemg_dataset_distribution_and_splits.png")
    combined.save(out_path)
    print("Created Diagram 2:", out_path)

    # Also copy individual files into diagrams folder
    shutil.copy(img1_path, os.path.join(DIAGRAMS_DIR, "eda_01_class_balance.png"))
    shutil.copy(img2_path, os.path.join(DIAGRAMS_DIR, "eda_02_splits.png"))

# ---------------------------------------------------------
# 4. TIMELINE DIAGRAM (Diagram 4)
# ---------------------------------------------------------
def create_timeline_diagram():
    fig, ax = plt.subplots(figsize=(15, 7.5), dpi=300)
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    ax.axis('off')
    ax.set_xlim(-1, 15)
    ax.set_ylim(0, 10)

    # Title
    ax.text(7, 9.4, "Timer-Driven Synchronization Timeline for Text, Video, and Audio", fontsize=16, fontweight='bold', ha='center', color='#2D3436')
    ax.text(7, 8.9, "Parallel Multimodal Execution: Audio Narration, Timer Ticks, CSS Highlight, Video Clips", fontsize=10, fontstyle='italic', ha='center', color='#636E72')

    # Time ticks
    ticks = [
        (0, "0 ms\n(Start)", "Token 0: Word 'the'\nSign Video", "#3498DB"),
        (3.2, "1350 ms\n(Tick 1)", "Token 1: Word 'CAT'\nFingerspell 'C'", "#E67E22"),
        (6.4, "2700 ms\n(Tick 2)", "Token 1: Word 'CAT'\nFingerspell 'A'", "#E67E22"),
        (9.6, "4050 ms\n(Tick 3)", "Token 1: Word 'CAT'\nFingerspell 'T'", "#E67E22"),
        (12.8, "5400 ms\n(End Units)", "700 ms Post-Roll Hold\n(Last Frame Displayed)", "#2ECC71")
    ]

    # Draw Time Line
    ax.plot([0, 13.5], [6.5, 6.5], color='#B2BEC3', lw=4, zorder=1)

    for x, label, detail, col in ticks:
        # Tick marker
        ax.plot([x, x], [6.2, 6.8], color=col, lw=3, zorder=2)
        ax.scatter([x], [6.5], color=col, s=100, zorder=3)
        # Tick time text
        ax.text(x, 7.1, label, fontsize=9.5, fontweight='bold', color=col, ha='center')

        # Box details below timeline
        bbox = patches.FancyBboxPatch((x-1.3, 4.3), 2.6, 1.7, boxstyle="round,pad=0.1", fc='#FFFFFF', ec=col, lw=1.8, zorder=3)
        ax.add_patch(bbox)
        ax.text(x, 5.15, detail, fontsize=8.5, ha='center', color='#2C3E50', fontweight='bold')

    # Channels / Parallel Tracks
    # Channel 1: Audio Speech Narration
    ax.text(-0.8, 3.2, "Audio Narration:", fontsize=10, fontweight='bold', color='#2C3E50', ha='right')
    ax.plot([0, 3.0], [3.2, 3.2], color='#3498DB', lw=6, solid_capstyle='round')
    ax.text(1.5, 3.2, "Utterance('the')", fontsize=8.5, color='#FFFFFF', fontweight='bold', ha='center', va='center')

    ax.plot([3.2, 6.2], [3.2, 3.2], color='#E67E22', lw=6, solid_capstyle='round')
    ax.text(4.7, 3.2, "Utterance('C.')", fontsize=8.5, color='#FFFFFF', fontweight='bold', ha='center', va='center')

    ax.plot([6.4, 9.4], [3.2, 3.2], color='#E67E22', lw=6, solid_capstyle='round')
    ax.text(7.9, 3.2, "Utterance('A.')", fontsize=8.5, color='#FFFFFF', fontweight='bold', ha='center', va='center')

    ax.plot([9.6, 12.6], [3.2, 3.2], color='#E67E22', lw=6, solid_capstyle='round')
    ax.text(11.1, 3.2, "Utterance('T.')", fontsize=8.5, color='#FFFFFF', fontweight='bold', ha='center', va='center')

    # Channel 2: Video src
    ax.text(-0.8, 2.0, "Video Clip Src:", fontsize=10, fontweight='bold', color='#2C3E50', ha='right')
    ax.text(1.5, 2.0, "/static/signs/the.mp4", fontsize=8.5, color='#2980B9', fontweight='bold', ha='center')
    ax.text(4.7, 2.0, ".../_letters/c.mp4", fontsize=8.5, color='#D35400', fontweight='bold', ha='center')
    ax.text(7.9, 2.0, ".../_letters/a.mp4", fontsize=8.5, color='#D35400', fontweight='bold', ha='center')
    ax.text(11.1, 2.0, ".../_letters/t.mp4", fontsize=8.5, color='#D35400', fontweight='bold', ha='center')
    ax.text(13.2, 2.0, "[700ms Hold]", fontsize=8.5, color='#27AE60', fontweight='bold', ha='center')

    # Channel 3: CSS Word/Letter Highlight
    ax.text(-0.8, 0.8, "Active Highlight:", fontsize=10, fontweight='bold', color='#2C3E50', ha='right')
    ax.text(1.5, 0.8, "Word Token #0 ('the')", fontsize=8.5, color='#34495E', ha='center')
    ax.text(4.7, 0.8, "Word #1 / Letter 'C'", fontsize=8.5, color='#34495E', ha='center')
    ax.text(7.9, 0.8, "Word #1 / Letter 'A'", fontsize=8.5, color='#34495E', ha='center')
    ax.text(11.1, 0.8, "Word #1 / Letter 'T'", fontsize=8.5, color='#34495E', ha='center')
    ax.text(13.2, 0.8, "Reset State", fontsize=8.5, color='#7F8C8D', ha='center')

    out_path = os.path.join(DIAGRAMS_DIR, "04_timer_driven_synchronization_timeline.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print("Created Diagram 4:", out_path)

# ---------------------------------------------------------
# COPY EXISTING DIAGRAMS (3, 5, 6, 7, 8)
# ---------------------------------------------------------
def copy_existing_diagrams():
    mapping = [
        (os.path.join(DOCS_FIG_DIR, "eda_05_augmentation_preview.png"), "03_eda_05_augmentation_preview.png", "eda_05_augmentation_preview.png"),
        (os.path.join(DOCS_FIG_DIR, "res_02_architecture_comparison.png"), "05_res_02_architecture_comparison.png", "res_02_architecture_comparison.png"),
        (os.path.join(DOCS_FIG_DIR, "res_03_ablation_study.png"), "06_res_03_ablation_study.png", "res_03_ablation_study.png"),
        (os.path.join(DOCS_FIG_DIR, "res_01_learning_curves.png"), "07_res_01_learning_curves.png", "res_01_learning_curves.png"),
        (os.path.join(DOCS_DIR, "confusion_matrix.png"), "08_confusion_matrix.png", "confusion_matrix.png"),
    ]

    for src, dst_numbered, dst_raw in mapping:
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DIAGRAMS_DIR, dst_numbered))
            shutil.copy(src, os.path.join(DIAGRAMS_DIR, dst_raw))
            print(f"Copied {os.path.basename(src)} -> {dst_numbered} & {dst_raw}")
        else:
            print(f"Warning: Source file {src} not found!")

if __name__ == "__main__":
    create_playback_engine_diagram()
    create_dataset_combined_diagram()
    create_timeline_diagram()
    copy_existing_diagrams()
    print("All diagram tasks completed successfully!")
