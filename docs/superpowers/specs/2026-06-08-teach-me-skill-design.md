# Teach Me Skill — Design Spec
**Date:** 2026-06-08
**Status:** Approved

---

## Overview

A skill that turns "I want to learn X" into a self-contained, multi-chapter course written to disk: markdown chapters with explanations, diagrams, worked examples, and quizzes, plus a separate answer key with reasoning, and (when possible) a combined PDF. The user picks the topic, depth (beginner/medium/advanced), and a few light preferences; the skill produces a structured outline, gets it approved, then writes the course chapter by chapter.

**Trigger phrases:** "teach me X", "I want to learn Y", "create a lesson on Z", "build me a course on...".

---

## Activation & Intake

The skill asks the following, one at a time (multiple choice where natural):

1. **Topic** — "What would you like to learn about?"
2. **Depth** — Beginner / Intermediate / Advanced
3. **Background** — light open-ended question on prior experience with the topic, used to calibrate tone and starting point (e.g. skip fundamentals for someone who already has them)
4. **Chapter count** — depth suggests a default the user can override:
   - Beginner ≈ 4 chapters
   - Intermediate ≈ 6 chapters
   - Advanced ≈ 8 chapters

   The skill states the suggested count and asks if the user wants more/fewer.
5. **Research-grounding (conditional offer)** — the skill judges whether the topic is fast-moving or fact-sensitive (e.g. "the latest framework APIs," current events, niche/contested subjects) versus stable (e.g. algebra, classic literature, established science). For the former, it offers an optional web-research pass that grounds chapter content in current sources and adds citations. For stable topics, it skips the offer and proceeds without asking.

The skill then confirms the plan in one line before generating anything: e.g. "Building a 6-chapter intermediate course on Python decorators, with research grounding — sound good?"

---

## Outline Phase & Approval Checkpoint

Before writing any files, the skill produces a course outline as a conversational summary:

- Course title
- One-line description of what the learner will be able to do by the end
- Numbered chapter list, each with a title and a one-sentence learning objective

It presents this and asks whether to proceed or adjust (reorder, merge, add/remove a chapter, change focus/emphasis). **No files are written until the user explicitly approves the outline.** This is the cheap point to redirect — far cheaper than revising fully-written chapters.

---

## Chapter Generation

Chapters are generated in order, each as its own file (`NN_<chapter-title-slug>.md`). Each chapter contains, in this order:

1. **Introduction** — what the chapter covers and why it matters
2. **Core content** — explanation scaled to the chosen depth:
   - Beginner: more analogies, gentler step-by-step buildup, simpler vocabulary
   - Intermediate: assumes basic fluency, balances theory and application
   - Advanced: dense, assumes fluency, emphasizes nuance, trade-offs, and edge cases
3. **Illustrations** — Mermaid diagrams or ASCII art embedded inline wherever a visual clarifies a concept (flowcharts, relationships, comparisons, timelines, mind maps). If an image-generation tool is available in the environment AND the concept is one that benefits from a generated image rather than a diagram (e.g. a visual metaphor, a historical scene), the skill offers to generate one and embeds/links it. Mermaid/ASCII is always the default — generated images are a bonus, never a dependency.
4. **Worked examples** — at least one concrete example illustrating each major concept introduced
5. **Key takeaways** — a short bullet-point recap of the chapter's main points
6. **Chapter quiz** — 3–5 questions (mix of multiple-choice and short-answer), placed at the end with **no answers included** in the chapter file

If research-grounding was opted into, factual claims in the core content carry inline citations/links to the sources found.

---

## Index & Answer Key

- **`00_index.md`** — written last (after all chapter files exist, so it can link to final titles): course title, one-paragraph description, full chapter list with links and learning objectives, and a short "how to use this course" note (e.g. suggesting the learner attempt each quiz before checking the answer key).
- **`ANSWERS.md`** — the master answer key, generated incrementally alongside each chapter (written in the same context that authored that chapter's quiz, so reasoning stays consistent and fresh). For every quiz question across all chapters: the correct answer, why it's correct, and — for multiple-choice — why the distractors are wrong. Kept as a separate document so it never spoils the learning flow.

---

## Output Layout

All output goes into a new folder in the current working directory:

```
lessons/<topic-slug>/
├── 00_index.md
├── 01_<chapter-title-slug>.md
├── 02_<chapter-title-slug>.md
├── ...
├── ANSWERS.md
└── <topic-slug>.pdf            (if PDF generation succeeds)
```

`<topic-slug>` is a kebab-case slug derived from the topic (e.g. "Python Decorators" → `python-decorators`).

---

## PDF Generation

After all markdown files are written:

1. Check whether `pandoc` is on `PATH`.
2. If missing, **ask the user for confirmation** before attempting to install it (e.g. `apt-get install -y pandoc`) — installing system packages is the kind of action that warrants a heads-up, not a silent attempt.
3. If pandoc is available (already present, or installed with consent): build the combined course PDF from `00_index.md` + all chapter files (in order), saved as `<topic-slug>.pdf`. `ANSWERS.md` stays a separate markdown document — it is not folded into the course PDF (consistent with keeping it spoiler-free and separate).
4. If pandoc isn't available and the user declines installation (or installation fails/isn't permitted): skip the PDF, tell the user the markdown set is the deliverable, and give them the exact `pandoc` command to run later themselves.

---

## Tone & Style

- Calibrate density and vocabulary to the chosen depth level — this is the single biggest lever on output quality
- Prefer concrete, worked examples over abstract description
- Use Mermaid/ASCII diagrams purposefully — only where a visual genuinely clarifies something a paragraph would belabor
- Quiz questions should test understanding and application, not just recall of definitions
- Answer-key reasoning should teach — explain *why*, not just state *what*

---

## Out of Scope

- No interactive quiz-taking within the chat (the quizzes are static markdown; the user self-grades against the answer key)
- No automatic updates/versioning of generated courses — each invocation produces a fresh, independent course folder
- Research-grounding is opt-in and topic-dependent, not a universal step
