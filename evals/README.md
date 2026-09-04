# Behavioral evaluations

These fixtures exercise decisions that deterministic syntax checks cannot prove
on their own. They are intentionally small project snapshots, not examples to
copy into production suites.

For an independent forward evaluation:

1. Give an agent the plugin checkout and ask it to perform a complete read-only
   audit of `evals/projects/semantic-reconciliation`.
2. Do not provide `evals/expected/semantic-reconciliation.md` or describe the
   planted failures.
3. Compare the final report with the expected decisions only after the agent
   finishes. Wording and headings do not matter; the semantic classifications
   do.

Run the deterministic regression fixture separately:

```bash
python scripts/run_evals.py
```

The runner uses only the bundled fallback checker and the standard library. It
does not install dependencies or execute the fixture project's application.
