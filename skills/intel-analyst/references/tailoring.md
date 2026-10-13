# Tailoring for Readers

How to produce a version of one product for each reader. Adapted from ODNI
ICD 208, *Maximizing the Utility of Analytic Products*.

## Reader profiles

| Profile | Who | Receives | File |
|---|---|---|---|
| `leadership` | Managers, executives, stakeholders who decide or fund | BLUF one-pager (`templates/bluf-one-pager.md`) | `docs/intel/YYYY-MM-DD-<slug>-bluf.md` |
| `engineers` | Peers who will review, implement, or challenge the work | Full product | `docs/intel/YYYY-MM-DD-<slug>.md` |
| `self` | The user, thinking through a problem | Full product plus a Working Notes appendix | `docs/intel/YYYY-MM-DD-<slug>.md` |

The full product is always written. A tailored file is written only for a
profile other than `engineers` and `self`. When `self` is among the readers,
the full product gets the Working Notes appendix, even if `engineers` is also
listed.

**Working Notes appendix (`self`):** rejected hypotheses and why, raw ACH
scoring before weighting, evidence that was collected but not used, and open
leads. Add it as a final `## Working Notes` section.

## Rules

1. Write and check the full product first. Derive tailored versions only after
   the full product passes the checklist in `analytic-standards.md`.
2. A tailored version may shorten, reorder, or omit. It must
   never add a judgment that is absent from the full product, and must never
   raise a probability or confidence.
3. Do not add estimates, quantities, durations, or comparisons that the full
   product does not state. Copy them; do not paraphrase them.
4. Keep the probability terms and confidence levels word for word. "Likely
   (moderate confidence)" stays "likely (moderate confidence)" in every version.
5. Every tailored version links to the full product with a relative link:
   `Full product: [<title>](./YYYY-MM-DD-<slug>.md)`.
6. Write for the reader's decision. For `leadership`: what to decide, by when,
   what it costs, and what could go wrong — each copied from the full product.
   If the full product states no cost, write "not estimated in the full
   product"; do not estimate one in the tailored version. Leave out the mechanism unless it
   changes the decision.
