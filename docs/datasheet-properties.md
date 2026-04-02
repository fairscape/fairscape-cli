# Datasheet Property Reference

The `fairscape-cli build datasheet` command generates an HTML datasheet from your RO-Crate metadata. This document lists every RO-Crate property that populates the datasheet, organized by section.

All properties are read from the **root entity** of the RO-Crate (the `ROCrateMetadataElem`).

---

## Overview Section

These properties populate the main overview panel of the datasheet.

| Datasheet Field | RO-Crate Property |
|---|---|
| Title | `name` |
| Description | `description` |
| Identifier | `@id` |
| DOI | `identifier` |
| License | `license` |
| Ethical Review | `ethicalReview` |
| Release Date | `datePublished` |
| Created Date | `dateCreated` |
| Updated Date | `dateModified` |
| Authors | `author` |
| Publisher | `publisher` |
| Principal Investigator | `principalInvestigator` |
| Contact Email | `contactEmail` |
| Copyright | `copyrightNotice` |
| Terms of Use | `conditionsOfAccess` |
| Confidentiality Level | `confidentialityLevel` |
| Citation | `citation` |
| Version | `version` |
| Content Size | `contentSize` |
| Funding | `funder` |
| Keywords | `keywords` |
| Related Publications | `associatedPublication` |
| Completeness | `completeness` |
| Human Subject | `humanSubjects` |
| Human Subject Research | `humanSubjectResearch` |
| Human Subject Exemptions | `humanSubjectExemption` |
| De-identified Samples | `deidentified` |
| FDA Regulated | `fdaRegulated` |
| IRB | `irb` |
| IRB Protocol ID | `irbProtocolId` |
| Data Governance | `dataGovernanceCommittee` |

### Property Details

??? note "Title — `name`"
    Human-readable name for the dataset.

??? note "Description — `description`"
    Human-readable description of the dataset.

??? note "Identifier — `@id`"
    Persistent unique identifier (ARK, URL, etc.).

    **Used in:** AI-Ready Findability and Sustainability scoring.

??? note "DOI — `identifier`"
    DOI or other external persistent identifier.

    **Used in:** AI-Ready Findability and Sustainability scoring.

??? note "License — `license`"
    Link to or name of the dataset license.

    **Example:** `https://creativecommons.org/licenses/by/4.0/`

    **Used in:** Distribution section, AI-Ready Fairness and Ethics scoring.

??? note "Ethical Review — `ethicalReview`"
    Were any ethical or compliance review processes conducted (e.g. by an IRB)?

    Describe the process, frequency of review, and outcomes.

    **Used in:** AI-Ready Ethics scoring.

??? note "Release Date — `datePublished`"
    Date the dataset was published or made publicly available (ISO 8601).

    **Used in:** Distribution section.

??? note "Created Date — `dateCreated`"
    Date the dataset was originally created (ISO 8601).

??? note "Updated Date — `dateModified`"
    Date the dataset was last modified (ISO 8601).

??? note "Authors — `author`"
    Who created the dataset — e.g. which team, research group, on behalf of which institution.

    **Format:** Parsed as list (comma or semicolon separated).

??? note "Publisher — `publisher`"
    Organization or person responsible for publishing or distributing the dataset.

    **Used in:** Distribution section, AI-Ready Computability scoring.

??? note "Principal Investigator — `principalInvestigator`"
    A key individual (PI) responsible for or overseeing dataset creation.

    **Used in:** AI-Ready Provenance scoring.

??? note "Contact Email — `contactEmail`"
    Email address for questions or correspondence about the dataset.

??? note "Copyright — `copyrightNotice`"
    Copyright statement including year and rights holder.

    **Example:** `Copyright (c) 2024 by The Regents of the University of California`

??? note "Terms of Use — `conditionsOfAccess`"
    Terms and conditions governing access to and use of this dataset.

    Includes any data use agreements required.

??? note "Confidentiality Level — `confidentialityLevel`"
    Access restriction classification.

    **Values:** `unrestricted`, `restricted`, or `confidential`.

    **Used in:** AI-Ready Ethics scoring.

??? note "Citation — `citation`"
    Preferred citation string for this dataset.

??? note "Version — `version`"
    Version string for this release (e.g. `1.0`, `2.3.1`).

    **Used in:** Distribution section.

??? note "Content Size — `contentSize`"
    Total size of the dataset content (e.g. `2.4 GB`).

    **Used in:** AI-Ready Characterization scoring.

??? note "Funding — `funder`"
    Who funded the creation of the dataset? Include grant names and numbers.

    **Format:** Parsed as list.

??? note "Keywords — `keywords`"
    Keywords or tags describing the dataset, used for discovery and search.

??? note "Related Publications — `associatedPublication`"
    Publication(s) associated with or describing this dataset.

    **Format:** Parsed as list.

??? note "Completeness — `completeness`"
    Assessment of how complete the dataset is relative to its intended scope — e.g. percentage of expected records present, known gaps.

    **Fallback:** `additionalProperty` with name "Completeness".

??? note "Human Subject — `humanSubjects`"
    Does this dataset involve human subjects? Indicate Yes/No and describe the nature of involvement.

    **Fallback:** `additionalProperty` with name "Human Subject".

    **Used in:** AI-Ready Ethics scoring.

??? note "Human Subject Research — `humanSubjectResearch`"
    Broader context for human subjects research involvement.

    Covers regulatory frameworks followed (e.g. 45 CFR 46, HIPAA).

    **Fallback:** `additionalProperty` with name "Human Subject Research".

??? note "Human Subject Exemptions — `humanSubjectExemption`"
    Applicable exemption category if human subjects research is exempt from full IRB review.

    **Example:** 45 CFR 46 Exemption 4.

    **Fallback:** `additionalProperty` with name "Human Subjects Exemptions".

??? note "De-identified Samples — `deidentified`"
    Whether the dataset has been de-identified to remove or obscure PII.

    Boolean converted to Yes/No.

    **Fallback:** `additionalProperty` with name "De-identified Samples".

??? note "FDA Regulated — `fdaRegulated`"
    Whether this dataset is subject to FDA regulations — e.g. clinical trial data, medical device data.

    Boolean converted to Yes/No.

    **Fallback:** `additionalProperty` with name "FDA Regulated".

??? note "IRB — `irb`"
    Institutional Review Board (IRB) information — covers approval status, approving institution, and contact details.

    Accepts a plain string or a structured IRB object.

    **Fallback:** `additionalProperty` with name "IRB".

??? note "IRB Protocol ID — `irbProtocolId`"
    IRB protocol identifier number assigned by the reviewing institution.

    **Fallback:** `additionalProperty` with name "IRB Protocol ID".

??? note "Data Governance — `dataGovernanceCommittee`"
    Name or contact for the data governance committee — responsible for oversight, access control, and policy enforcement.

    **Fallback:** `additionalProperty` with name "Data Governance Committee".

    **Used in:** AI-Ready Ethics and Sustainability scoring.

### additionalProperty Fallbacks

Several human-subjects and governance fields support a fallback mechanism. If the top-level property is not set, the converter checks the `additionalProperty` array for a matching `name` entry:

```json
{
  "additionalProperty": [
    {"name": "Human Subject", "value": "Yes"},
    {"name": "Data Governance Committee", "value": "Bridge2AI Ethics Committee"}
  ]
}
```

---

## Use Cases Section

These properties populate the responsible AI (RAI) and data documentation panel. RAI properties conform to the [Croissant RAI 1.0 specification](http://mlcommons.org/croissant/RAI/1.0). A dataset can declare conformance by setting `dct:conformsTo: "http://mlcommons.org/croissant/RAI/1.0"` at the root entity level.

| Datasheet Field | RO-Crate Property | Croissant RAI Use Case |
|---|---|---|
| Intended Use | `rai:dataUseCases` | AI safety and fairness, Compliance |
| Limitations | `rai:dataLimitations` | AI safety and fairness |
| Prohibited Uses | `prohibitedUses` | Compliance |
| Potential Sources of Bias | `rai:dataBiases` | AI safety and fairness |
| Maintenance Plan | `rai:dataReleaseMaintenancePlan` | Compliance, Data life cycle |
| Data Collection | `rai:dataCollection` | Data life cycle |
| Data Collection Type | `rai:dataCollectionType` | Data life cycle |
| Data Collection Missing Data | `rai:dataCollectionMissingData` | Data life cycle |
| Data Collection Raw Data | `rai:dataCollectionRawData` | Data life cycle |
| Data Collection Timeframe | `rai:dataCollectionTimeframe` | Data life cycle |
| Data Imputation Protocol | `rai:dataImputationProtocol` | Compliance |
| Data Manipulation Protocol | `rai:dataManipulationProtocol` | Compliance |
| Data Preprocessing Protocol | `rai:dataPreprocessingProtocol` | Data life cycle |
| Data Annotation Protocol | `rai:dataAnnotationProtocol` | Data labeling, Compliance |
| Data Annotation Platform | `rai:dataAnnotationPlatform` | Data labeling, Participatory data |
| Data Annotation Analysis | `rai:dataAnnotationAnalysis` | Data labeling, Compliance |
| Personal/Sensitive Information | `rai:personalSensitiveInformation` | Compliance, AI safety and fairness |
| Data Social Impact | `rai:dataSocialImpact` | AI safety and fairness |
| Annotations Per Item | `rai:annotationsPerItem` | Data labeling |
| Annotator Demographics | `rai:annotatorDemographics` | Data labeling, Participatory data, Inclusion |
| Machine Annotation Tools | `rai:machineAnnotationTools` | Data labeling |

### Property Details

??? note "Intended Use — `rai:dataUseCases`"
    Explicit statement of intended uses.

    **Values:** Training, Testing, Validation, Development or Production Use, Fine Tuning, others.

    Include usage guidelines and caveats.

    **Used in:** AI-Ready Pre-Model Explainability scoring.

??? note "Limitations — `rai:dataLimitations`"
    Known limitations of the dataset.

    Covers data generalization limits (e.g. related to data distribution or quality) and non-recommended uses. Distinct from biases (systematic errors) and anomalies (data quality issues).

    **Used in:** AI-Ready Pre-Model Explainability scoring.

??? note "Prohibited Uses — `prohibitedUses`"
    Explicit statement of uses not permitted by license, ethics, or policy. Stronger than discouraged uses.

    **Fallback:** `additionalProperty` with name "Prohibited Uses".

    **Used in:** AI-Ready Ethics scoring.

??? note "Potential Sources of Bias — `rai:dataBiases`"
    Known biases in the dataset — systematic errors or prejudices that may affect representativeness or fairness.

    Distinct from anomalies (data quality issues) and limitations (scope constraints).

    **Used in:** AI-Ready Characterization scoring.

??? note "Maintenance Plan — `rai:dataReleaseMaintenancePlan`"
    Will the dataset be updated? If so, how often and by whom?

    Cover versioning timeframe, maintainers, how updates are communicated, and deprecation policies.

    **Used in:** AI-Ready Sustainability scoring.

??? note "Data Collection — `rai:dataCollection`"
    What mechanisms or procedures were used to collect the data?

    **Examples:** Hardware sensors, manual curation, software APIs. Also covers how these mechanisms were validated.

    **Used in:** AI-Ready Ethics scoring.

??? note "Data Collection Type — `rai:dataCollectionType`"
    List of collection type(s), joined to string.

    **Recommended values:** Surveys, Secondary Data Analysis, Physical Data Collection, Direct Measurement, Document Analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus Groups, Self-Reporting, Customer Feedback Data, User-Generated Content Data, Passive Data Collection, Others.

??? note "Data Collection Missing Data — `rai:dataCollectionMissingData`"
    Document missing data patterns and handling strategies.

    Cover pattern types (MCAR, MAR, MNAR), known or suspected causes (e.g. sensor failures, participant dropout, privacy constraints), and strategies used to handle missing values.

    **Used in:** AI-Ready Characterization scoring.

??? note "Data Collection Raw Data — `rai:dataCollectionRawData`"
    Description of raw data sources before preprocessing or labeling.

    Document where the original data comes from and how it can be accessed.

??? note "Data Collection Timeframe — `rai:dataCollectionTimeframe`"
    Over what timeframe was the data collected? Does this timeframe match the creation timeframe of the underlying data?

    Provide start and end dates where possible. List joined to string.

??? note "Data Imputation Protocol — `rai:dataImputationProtocol`"
    Describe data imputation methodology.

    Cover techniques used (e.g. mean/median imputation, forward fill, model-based imputation) and rationale for chosen approaches.

??? note "Data Manipulation Protocol — `rai:dataManipulationProtocol`"
    Was any cleaning done? Describe the procedures applied.

    **Examples:** Removal of instances, processing of missing values, deduplication, filtering.

??? note "Data Preprocessing Protocol — `rai:dataPreprocessingProtocol`"
    Was any preprocessing done? Describe steps to make the data ML-ready.

    **Examples:** Discretization or bucketing, tokenization, feature extraction, normalization. List joined to string.

??? note "Data Annotation Protocol — `rai:dataAnnotationProtocol`"
    Annotation methodology, tasks, and protocols.

    Include annotation guidelines, quality control procedures, task definitions, workforce type, annotation characteristics, and label distributions.

??? note "Data Annotation Platform — `rai:dataAnnotationPlatform`"
    Platform or tool used for annotation.

    **Examples:** Label Studio, Prodigy, Amazon Mechanical Turk, custom annotation tool. List joined to string.

??? note "Data Annotation Analysis — `rai:dataAnnotationAnalysis`"
    Analysis of annotation quality and inter-annotator agreement.

    Cover metrics used (e.g. Cohen's kappa, Fleiss' kappa), systematic disagreements between annotators of different socio-demographic groups, and how final labels relate to individual annotator responses. List joined to string.

??? note "Personal/Sensitive Information — `rai:personalSensitiveInformation`"
    Does the dataset contain sensitive data?

    **Attribute types:** Gender, Socio-economic status, Geography, Language, Age, Culture, Experience or Seniority, others. List joined to string.

    **Used in:** AI-Ready Ethics scoring.

??? note "Data Social Impact — `rai:dataSocialImpact`"
    Describe potential social impacts and mitigation strategies.

    Is there anything about the dataset's composition or collection that might impact future uses or create risks/harm (e.g. unfair treatment, legal or financial risks)?

??? note "Annotations Per Item — `rai:annotationsPerItem`"
    Number of annotations collected per data item.

    Multiple annotations per item enable calculation of inter-annotator agreement.

??? note "Annotator Demographics — `rai:annotatorDemographics`"
    Demographic information about annotators, if available.

    **Examples:** Geographic location, language background, expertise level, age group, gender. List joined to string.

??? note "Machine Annotation Tools — `rai:machineAnnotationTools`"
    Automated or ML-based annotation tools used.

    **Examples:** NLP pipelines, computer vision models. Format each entry as `ToolName version` (e.g. `spaCy 3.5.0`). List joined to string.

---

## Distribution Section

These properties populate the distribution/access panel.

| Datasheet Field | RO-Crate Property | Notes |
|---|---|---|
| License | `license` | Same property as Overview |
| Publisher | `publisher` | Same property as Overview |
| DOI | `doi` | |
| Release Date | `datePublished` | Same property as Overview |
| Version | `version` | Same property as Overview |

---

## Summary Section (AI-Ready Score)

The summary section displays the computed AI-Ready score. See [AI-Ready Scoring Reference](ai-ready-scoring.md) for the full breakdown of which properties affect each scoring criterion.
