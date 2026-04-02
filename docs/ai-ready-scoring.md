# AI-Ready Scoring Reference

The AI-Ready score evaluates how well an RO-Crate meets criteria for responsible, reproducible AI research. It is computed across 7 categories with 28 sub-criteria.

Each sub-criterion is scored as either **met** (property present with content) or **not met** (missing/empty). Some criteria are **inferred** from the RO-Crate structure itself and are always met.

For release-level RO-Crates, aggregated metrics (`evi:*` properties) are used when available, falling back to counting entities in the metadata graph.

---

## 0. Fairness (FAIR Principles)

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Findable | `identifier` (DOI), `@id` | Direct -- checks DOI first, falls back to @id |
| Accessible | -- | Inferred (always met: RO-Crate is machine-readable) |
| Interoperable | -- | Inferred (always met: schema.org + RO-Crate standard) |
| Reusable | `license` | Direct |

## 1. Provenance

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Transparent | Count of Dataset entities (or `evi:datasetCount`) | Counted |
| Traceable | Count of Computation + Experiment entities (or `evi:computationCount`) | Counted |
| Interpretable | Count of Software entities (or `evi:softwareCount`) | Counted |
| Key Actors Identified | `author`, `publisher`, `principalInvestigator` | Direct -- any combination triggers |

## 2. Characterization

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Semantics | -- | Inferred (always met: RO-Crate provides semantic context) |
| Statistics | `contentSize`, `hasSummaryStatistics` (or `evi:totalContentSizeBytes`, `evi:entitiesWithSummaryStats`) | Counted -- checks total size and summary stats availability |
| Standards | Count of Schema entities (or `evi:schemaCount`) | Counted |
| Potential Sources of Bias | `rai:dataBiases` | Direct |
| Data Quality | `rai:dataCollectionMissingData` | Direct |

## 3. Pre-Model Explainability

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Data Documentation Template | `dct:conformsTo` | Inferred (always met: RO-Crate + [Croissant RAI 1.0](http://mlcommons.org/croissant/RAI/1.0)). Optional: set `dct:conformsTo: "http://mlcommons.org/croissant/RAI/1.0"` on the root entity to declare explicit conformance |
| Fit for Purpose | `rai:dataUseCases`, `rai:dataLimitations` | Direct -- either triggers |
| Verifiable | `md5`, `MD5`, `sha256`, `SHA256`, `hash` on Dataset/Software entities (or `evi:totalEntities`, `evi:entitiesWithChecksums`) | Counted -- reports percentage of files with checksums |

## 4. Ethics

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Ethically Acquired | `rai:dataCollection`, `humanSubjects` (fallback: `additionalProperty` "Human Subject") | Direct -- either triggers |
| Ethically Managed | `ethicalReview`, `dataGovernanceCommittee` (fallback: `additionalProperty` "Data Governance Committee") | Direct -- either triggers |
| Ethically Disseminated | `license`, `rai:personalSensitiveInformation`, `prohibitedUses` (fallback: `additionalProperty` "Prohibited Uses") | Direct -- any combination triggers |
| Secure | `confidentialityLevel` | Direct |

## 5. Sustainability

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Persistent | `identifier` (DOI), `@id` | Direct -- checks DOI first, falls back to @id |
| Domain Appropriate | `rai:dataReleaseMaintenancePlan` | Direct |
| Well Governed | `dataGovernanceCommittee` (fallback: `additionalProperty` "Data Governance Committee") | Direct |
| Associated | -- | Inferred (always met: RO-Crate links all components) |

## 6. Computability

| Sub-criterion | Properties Checked | Logic |
|---|---|---|
| Standardized | `format` values across Dataset/Software entities (or `evi:formats`) | Counted -- lists up to 5 unique formats |
| Computationally Accessible | `publisher` | Direct |
| Portable | -- | Inferred (always met: RO-Crate standard) |
| Contextualized | -- | Inferred (always met: RO-Crate graph structure) |

---

## Cross-Reference: Properties That Affect Both Datasheet and Scoring

These properties appear in the datasheet **and** influence the AI-Ready score. Filling them in gives you the most value.

| RO-Crate Property | Datasheet Section(s) | AI-Ready Category |
|---|---|---|
| `@id` | Overview | Fairness (findable), Sustainability (persistent) |
| `identifier` (DOI) | Overview | Fairness (findable), Sustainability (persistent) |
| `license` | Overview, Distribution | Fairness (reusable), Ethics (ethically disseminated) |
| `author` | Overview | Provenance (key actors) |
| `publisher` | Overview, Distribution | Provenance (key actors), Computability (computationally accessible) |
| `principalInvestigator` | Overview | Provenance (key actors) |
| `contentSize` | Overview | Characterization (statistics) |
| `confidentialityLevel` | Overview | Ethics (secure) |
| `ethicalReview` | Overview | Ethics (ethically managed) |
| `dataGovernanceCommittee` | Overview | Ethics (ethically managed), Sustainability (well governed) |
| `humanSubjects` | Overview | Ethics (ethically acquired) |
| `rai:dataBiases` | Use Cases | Characterization (bias) |
| `rai:dataCollectionMissingData` | Use Cases | Characterization (data quality) |
| `rai:dataUseCases` | Use Cases | Pre-Model Explainability (fit for purpose) |
| `rai:dataLimitations` | Use Cases | Pre-Model Explainability (fit for purpose) |
| `rai:dataCollection` | Use Cases | Ethics (ethically acquired) |
| `rai:personalSensitiveInformation` | Use Cases | Ethics (ethically disseminated) |
| `prohibitedUses` | Use Cases | Ethics (ethically disseminated) |
| `rai:dataReleaseMaintenancePlan` | Use Cases | Sustainability (domain appropriate) |

---

## Properties That Only Affect AI-Ready Score

These properties are **not** shown on the datasheet but do influence scoring:

| Property | AI-Ready Category | Notes |
|---|---|---|
| `hasSummaryStatistics` | Characterization (statistics) | Reference to a summary stats entity |
| `md5` / `sha256` / `hash` | Pre-Model Explainability (verifiable) | On individual Dataset/Software entities |
| `format` | Computability (standardized) | On individual Dataset/Software entities |
| Entity counts (Dataset, Software, Computation, Experiment, Schema) | Provenance, Characterization | Counted from metadata graph or `evi:*` aggregates |

### Aggregated Release Metrics (`evi:*` properties)

For release-level RO-Crates, these pre-aggregated properties are checked first:

| Property | Replaces |
|---|---|
| `evi:datasetCount` | Counting Dataset entities |
| `evi:computationCount` | Counting Computation/Experiment entities |
| `evi:softwareCount` | Counting Software entities |
| `evi:schemaCount` | Counting Schema entities |
| `evi:totalContentSizeBytes` | Summing contentSize across entities |
| `evi:entitiesWithSummaryStats` | Counting entities with hasSummaryStatistics |
| `evi:totalEntities` | Counting Dataset/Software entities for checksum percentage |
| `evi:entitiesWithChecksums` | Counting entities with md5/sha256/hash |
| `evi:formats` | Collecting unique format values |
