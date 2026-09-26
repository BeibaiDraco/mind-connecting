# Illustration handoff and print-size check

2026-09-25, Codex. Generated according to A1–A6 in `paper/figures/codex_handoff.md` and sections 7–12 of `imagegen_prompts.md`, including the optional A5. Used the built-in `image_gen.imagegen` (GPT image model; the tool does not disclose the exact model ID), with 18 generations and revisions in total. The illustrations are only schematic; the statistical figures and numbers come from the existing figure scripts and the raw records.

The initial prompts are saved in `handoff_20260925_prompts.json`; each actual prompt, the edit reference image paths, the source output paths, the selected version and the final SHA256 are saved in `handoff_20260925_manifest.json`. The final files were copied directly from the tool output, with no image editing in Python or any other program; all are solid-background RGB PNGs.

| Handoff item | Final file | Selected version | Pixel size | Main checks and revisions |
|---|---|---|---|---|
| A1 | `fig1d_v1.png` | 3 | 2033 × 773 | Enlarged the text of the speech bubble and the tower/table cards; orange B sends content into blue A. |
| A2 | `fig1e_v1.png` | 4 | 1942 × 809 | To avoid small text, the full reflection is shown once at the top, shared, and connected to the same A notes before and after the link cut; both answers branch out from A. The original text contains speed and dragon, and the answers after the link cut contain lowest cost and dragon. |
| A3 | `fig1f_v1.png` | 3 | 1942 × 809 | Enlarged the original cards and the swapped answers; blue/orange attribution is consistent, and the two-way arrows are clear. |
| A4 | `task_v2.png` | 2 | 1817 × 866 | Changed to an opaque white background; the question card points into A, so the question is not drawn as A's own speech; B's code word is dragon; no correct-answer check mark; Robin appears on both sides, and the small squares are labeled as reflection tokens. |
| A5 | `channel_v2.png` | 2 | 2172 × 724 | The four routes carry no raster titles; the compact strip can have its white margins cropped by the existing script, and the titles come from the script's vector text. |
| A6 | `pairs_v2.png` | 4 | 1536 × 1024 | Corrected the arrow start points: the fixed path starts from the cards, the live path starts from the reflection tokens, and both go to the other model; enlarged the text and used a white background. |

Rerun command (the figure code was not modified):

```bash
MB_DATA_ROOT='/Volumes/VERBATIM SD/mind-connecting-data' .venv/bin/python scripts/make_story_figures.py
```

Each of the six final `paper/figures/fig*.png` figures was viewed one by one; in addition, the six PDFs were rendered at 6.5 inches wide and 144 dpi, to check text size in the actual panels, spacing between lines and text, arrow attribution and cropping. No text overlapping lines, clipped text, or labels landing on the wrong object were seen; the smallest, Fig 1e, uses larger shared note text and is still legible when shrunk to the final figure size. This check was a print-size check on screen; no physical printing is claimed.

The 21 pages of `paper/main.pdf` were also rendered at 120 dpi and checked page by page: main text 9 pages, references 3 pages, appendix 9 pages. The scripts, `story_numbers.json` and the result files were not changed; all data figures were rebuilt by the original scripts.

**Wording inside a figure, left for Claude:** the vector title of Fig 1d is still "Claims B’s word, notices nothing" and should be changed to "Claims B’s word, reports no anomaly" or an equivalent short phrase. This is not text inside a GPT illustration, so per the division of labor a message was left in STATUS and the code was not changed. Also, the gray dashed return line in Fig 1c mentioned in the handoff checklist does not exist in the actual figure; the caption was written for the current figure's one-way orange arrow.
