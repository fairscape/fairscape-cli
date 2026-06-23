"""Local-filesystem adapters for the fairscape_graph_tools pipeline.

Implements the four ports (`GraphSource`, `ResultSink`, `TaskTracker`,
`SoftwareFetcher`) against local RO-Crate directories, so the shared
interpretation pipeline can run from `fairscape interpret <path>`
without a Mongo server or bearer token in sight. Source crates are
never modified -- results are always written as sidecar JSON.
"""
