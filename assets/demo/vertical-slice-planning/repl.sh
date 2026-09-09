#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic vertical-slice-planning pass (seam map → slice ordering →
# emitted directory → --status probe, mirroring
# skills/vertical-slice-planning/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

p "I'm using the vertical-slice-planning skill to create the plan." 0.7
echo
p "Seam map — components, and the seams between them:" 0.25
p "  client -> orders HTTP    client        -> svc/orders" 0.2
p "  orders -> jobs queue     svc/orders    -> worker/jobs" 0.6
echo
p "Ordering as vertical slices (T2 wherever a task crosses a seam):" 0.25
p "  01  Wire retry header end-to-end       T2  client, svc/orders" 0.2
p "  02  Persist retry count on the order   T1  svc/orders" 0.2
p "  03  Emit retry job across the queue    T2  svc/orders, worker/jobs" 0.2
p "  04  Backoff policy + real payloads     T2  all three" 0.6
echo
p "Task 01 carries a hardcoded header and one assertion — the thinnest" 0.2
p "payload that still proves the seam. Later tasks thicken it." 0.7
echo
p "Emitting docs/plans/2026-09-08-retry-header/ ..." 0.4
p "  + plan.md, plan_superpowers.md" 0.2
p "  + taskkit.py, run.py            (copied verbatim)" 0.2
p "  + tasks/task_01_wire_seam.py    apply() via hashline, verify() T0+T1+T2" 0.2
p "  + tasks/task_02..04_*.py" 0.8
echo
printf '$ python3 docs/plans/2026-09-08-retry-header/run.py --status\n'
sleep 0.8
p "task_01_wire_seam.py                     GATE FAILED" 0.3
p "task_02_persist_retry_count.py           GATE FAILED" 0.3
p "task_03_emit_retry_job.py                GATE FAILED" 0.3
p "task_04_backoff_policy.py                GATE FAILED" 0.6
p "0/4 gates green (4 checkbox lines updated)" 0.5
echo
p "Every gate is red because nothing has been applied yet — that is the" 0.2
p "point. Plan only: execution is a separate act." 1.0
