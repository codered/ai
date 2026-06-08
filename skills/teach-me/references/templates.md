# Output Templates

Exact templates for the three kinds of files this skill produces. Copy the structure;
fill in the bracketed placeholders. Don't drop a section — if something genuinely
doesn't apply, write "N/A — [reason]" rather than omitting it.

---

## Chapter Template

Used for every `NN_<chapter-title-slug>.md` file.

```markdown
# Chapter [N]: [Chapter Title]

## Introduction

[2-4 sentences: what this chapter covers and why it matters to the learner's overall
goal for the course.]

## [Core Content Section 1 Title]

[Explanation scaled to the course's depth level. Define new terms on first use. Use
sub-headings (###) to break up long sections.]

```mermaid
[A diagram only if it clarifies this concept faster than prose — flowchart, sequence,
mindmap, etc. Omit this block entirely if no diagram earns its place here.]
```

## [Core Content Section 2 Title]

[Continue building on the previous section. Keep section count proportional to the
chapter's scope — most chapters need 2-4 core content sections.]

## Worked Example: [Example Title]

[A complete, concrete example demonstrating the concept just introduced. Show it in
full — no "..." truncation. Walk through what's happening and why.]

## Key Takeaways

- [Main point 1]
- [Main point 2]
- [Main point 3]
[3-6 bullets total — the chapter's core ideas in compressed form.]

## Quiz

1. [Question 1 — multiple choice or short answer]
   [If multiple choice, list options as a) b) c) d)]
2. [Question 2]
3. [Question 3]
[3-5 questions total. Do not include answers here — see ANSWERS.md.]
```

---

## Index Template

Used for `00_index.md`. Written last, once every chapter and `ANSWERS.md` exist.

```markdown
# [Course Title]

[One-paragraph description: what this course covers and what the learner will be able
to do by the end of it.]

## Chapters

1. **[Chapter 1 Title](01_<chapter-title-slug>.md)** — [one-sentence learning objective]
2. **[Chapter 2 Title](02_<chapter-title-slug>.md)** — [one-sentence learning objective]
[... one entry per chapter, in order, linking to the actual filenames used.]

## How to Use This Course

- Work through the chapters in order — later chapters build on earlier ones.
- Attempt each chapter's quiz before looking anything up.
- Check your answers against [`ANSWERS.md`](ANSWERS.md), which explains the reasoning
  behind each answer — read the reasoning even for questions you got right.
[Add any course-specific guidance here, e.g. suggested pacing or prerequisite notes.]
```

---

## Answer Key Template

Used for `ANSWERS.md`. Built incrementally — append each chapter's answers right after
writing that chapter, in the same context that wrote its quiz.

```markdown
# Answer Key

Reasoning-first answers for every chapter quiz in this course. Try each quiz yourself
before reading the explanation — the reasoning is the point, not just the answer.

## Chapter 1: [Chapter Title]

**1. [Restate the question]**

Answer: [The correct answer]

Why: [Explain *why* this is correct — the reasoning a learner should walk away with.
For multiple-choice questions, also explain why each distractor is wrong: "B is
tempting because [...], but it's incorrect because [...]".]

**2. [Restate the question]**

Answer: [...]

Why: [...]

[Continue for every question in the chapter, then start a new `## Chapter N: [Title]`
section for the next chapter's answers.]
```
