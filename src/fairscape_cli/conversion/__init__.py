"""Datasheet + D4D mapping modules the CLI owns outright.

These were `fairscape_models.conversion.mapping.FairscapeDatasheet`,
`.mapping.subcrate_utils`, `.mapping.d4d` and `.models.FairscapeDatasheet`.
They were cut from `fairscape_models` (2026-09-22) because the CLI was their
only consumer: the datasheet and AI-readiness work now lives in
`fairscape_artifacts`, and RO-Crate <-> D4D in `fairscape_conversion.plugins.d4d`.

They are copied here verbatim so the CLI keeps working, and are free to drift
from whatever the rest of the stack does. Nothing outside `fairscape_cli`
imports them.

Still coming from `fairscape_models.conversion` (kept there for fairscape_server):
`converter.ROCToTargetConverter`, `mapping.croissant`, `mapping.AIReady`,
`models.AIReady`. When those are eventually cut too, vendor them here the same way.
"""
