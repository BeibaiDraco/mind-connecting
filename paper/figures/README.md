# Paper figures

## Figure 1 · Three-panel concept figure (vector cartoon version)

- Files: `fig1_concept.pdf` (for use in the paper, 5.5 in × 1.96 in, equal to the ICLR text width), `fig1_concept.svg` (editable source file, text not converted to outlines), `fig1_concept.png` (2640 px preview).
- To regenerate: `python3 paper/figures/fig1_concept.py`. Uses only the standard library; requires `rsvg-convert` and Ghostscript (`brew install librsvg ghostscript`). Text in the PDF has been converted to outlines and contains no fonts, to avoid Type 3 fonts.
- Fonts: Arial Rounded MT Bold, Chalkboard SE, Menlo (bundled with macOS).
- This and `docs/figures/figure1_concept_v1.png` (Codex, imagegen bitmap, more realistic) are two versions of the same figure; the PI chooses one of the two.

Meaning of the elements in the figure:
- (a) A brain connects to a computer through an electrode interface and wires, and the thought "Hi!" appears on the screen.
- (b) Two brains are connected through the same bridging device. The orange and the snowflake represent each one's private thought, and each brain is wondering "which one is mine". The question marks, "consciousness?", "self?" and 🤔 indicate that these are open questions.
- (c) Two copies A and B of the same model. The five horizontal bars on the chest indicate layers, and the yellow layer connects through the bridging device to the same layer of the other. "mine or yours?" is the question this paper can test. The orange and the snowflake are taken from the code-name words orange and winter in the experimental word list.

### Draft English caption

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/fig1_concept.pdf}
  \caption{\textbf{From brain--machine interfaces to a testable question about the self.}
  \textbf{(a)}~A brain--computer interface links one brain to a machine.
  \textbf{(b)}~A thought experiment: bridge two brains, each holding a private thought
  (orange, snowflake). Whose thought is whose, and what happens to the self?
  \textbf{(c)}~This work: two copies of the same LLM (A, B), each holding private content,
  exchange hidden states at one layer through a training-free bridge. We ask whether each copy
  can still tell its own content from its partner's (``mine or yours?'').
  We study functional source attribution only and make no claims about consciousness.}
  \label{fig:concept}
\end{figure}
```

### Scope of use

A schematic that presents no results. (b) is a thought experiment and does not mean any human two-brain experiment was done. The number of layers in (c), the look of the bridging device, and the two colors of small balls on the wires (indicating two-way transfer) are all only schematic; the actual method is as given in sections 5–7 of protocol v0.5.

AI use statement (to go into the corresponding section of the paper): this figure was generated from plotting code written by Claude Code; every element is a vector graphic drawn by code, and no image generation model was used. The authors are responsible for checking the scientific content of the figure.
