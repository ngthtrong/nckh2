# Paper 6444 presentation: source and interpretation audit

Prepared 2026-11-07. Scope: source-bound adaptation of the supplied manuscript into the user-approved 26-slide conference outline. No manuscript edits, new benchmark batch, scientific acceptance decision, or external manuscript upload was performed by this task.

## Authority and author metadata

- Canonical title: **Stress-Testing Product-Gated Clustering and Bounded Priority Ranking for Flood-Rescue Reports: A Synthetic Study** (`paper/main.tex:61–62`).
- Current title page has eight authors (`paper/main.tex:62–72`): Thanh-Trong Nguyen; Ngoc-Anh Le; Nhu-Quynh Nguyen; Tuong-Hung Cao; Hung-Thinh Ngo; Xuan-Phuong Chau; Lan Phuong Phan; Thanh-Khoa Nguyen.
- Current manuscript marks **Thanh-Khoa Nguyen** as corresponding author (`paper/main.tex:72`). Older camera-ready notes in the repository differ; they do not override the current source.
- Affiliation: College of Information and Communication Technology, Can Tho University, Can Tho, Vietnam (`paper/main.tex:74–75`).
- Funding: Can Tho University, Code **THS2026-68** (`paper/main.tex:803–804`, exact source text checked).
- Archived artifact metadata lists six creators; that is historical release metadata and must not replace the current eight-author title page.

## Claims and local locators

| Slide(s) | Source locator | Supported content and boundary |
|---|---|---|
| 3–5 | `paper/main.tex:110–188` | Motivation, gap, pipeline and contributions. Report consolidation is different from incident truth. Scheduler uses predicted clusters; evaluator truth joins after schedule fixation. |
| 6 | `paper/main.tex:441–454`; `thucnghiem/data/README.md`; `thucnghiem/data/gold/run_001/run_manifest.json` | Generator 3.0 is geographically anchored **semi-synthetic**: EMSR848 context, OSM anchors, WorldPop reference population. Incidents, reports, duplicates, campaigns, vulnerability and labels are simulated. 80 runs; 16 incidents/run; 26,288 reports =17,901 genuine+3,587 duplicate+4,800 coordinated nonincident reports. Population reference is not observed trapped-person truth. Manifest describes assumed image evidence but no generated bitmap images. Raw source snapshots and row-level source lineage are unavailable. |
| 7 | `paper/main.tex:456–469` | Candidate 4.1 is **separate and fully synthetic**. 80 datasets; 16 incidents/dataset; 30,229 reports; development/calibration/test seeds1000–1019/2000–2019/3000–3039. No EMSR848-anchoring claim. Two artifact suites are not a common-sample end-to-end chain. |
| 8 | `paper/main.tex:250–325` | Product=`a_i a_j G_ij(beta T_ij+gamma C_ij)`; Additive=`a_i a_j(alpha G_ij+beta T_ij+gamma C_ij)`. G Gaussian in geographic distance; T exponential in time difference; C contextual similarity. Conditional retained-edge bound does not bound entire cluster diameter without a hop-diameter condition; long chains remain possible. |
| 9 | `paper/main.tex:128–141`; Blondel et al. primary paper | Product/Additive construct graph weights; Louvain detects communities. Louvain optimizes modularity approximately by local movement and aggregation. Modularity is not incident-label accuracy. Any small pedagogical GIF must be labeled schematic. |
| 10 | `paper/main.tex:380–421` | Fixed evidence families, family maxima, clipped claims, log normalization and saturated vulnerability. Score0≤P≤mu,1≤mu≤2. Reference constantsomega(.34,.33,.33),mu2,s10,N_ref500,V_cap50. Copy invariance is conditional on fixed grouping and score inputs. Q is a heuristic, not a calibrated probability of truth (`paper/main.tex:195–224`). |
| 11–12 | `paper/main.tex:150–168,486–543` | Formal RQs; independent calibration; oracle grouping for RQ2; predicted clusters for RQ3. 20/20/40 splits. RQ3 primary inference averages three resource conditions within each of40seeds. No120-independent-sample claim. |
| 13 | `paper/main.tex:522–543`; Hubert&Arabie; scikit-learn ARI docs | ARI corrects partition agreement for chance;1perfect,0chance expectation,negativepossible; not percent correct. PairwiseF1 balances pair precision and recall. Fixed-copy stress evaluates original incident-linked reports. |
| 14 | `thucnghiem/results/RQ2_Priority_Robustness_Colab.ipynb`, code cell4 (zero-based), `independent_benefit`, `alignment_rows_for_seed`; `paper/main.tex:622–677` | Relevance is nonnegative independent benefit, computed as max(0,H(response480)-H(response0)) in RQ2. Notebook calls `ndcg_score([relevance],[predicted],k=5)` with **linear raw gain**, not `2**relevance-1`. DCG=sum benefit_rank/log2(rank+1); divide by idealDCG. Tied scores use the library's default tie handling. Spearman and top5overlap are descriptive alignment endpoints. Prioritydrift and rankdrift are normalized; churn concerns top5membership. |
| 15 | `thucnghiem/results/RQ3_EndToEnd_Dispatch_Colab.ipynb`, code cell6 (zero-based), `harm` and `evaluate_schedule`; `paper/main.tex:679–708` | RQ3 harm=slope*max(0,response-deadline-grace)+capacity_penalty*max(0,service_demand/service_rate-capacity). Deadline miss is `response > deadline`, **not completion-time** deadline comparison. Unserved response uses480-minutehorizon. RQ3 harm differs from the RQ2 benefit helper, which includes service in its completion variable. Harm is model units, not lives/injuries/monetary losses. |
| 16 | `paper/main.tex:548–591` | AdditiveLouvain ARI.9191 CI[.8995,.9381]; ProductLouvain.9072 CI[.8864,.9271]; ProductLeiden.9165; Convex.9135; matched-densityAdditive.8973. Product-minus-tunedAdditive=-.01184 unadjustedbootstrapCI[-.02257,-.00240], adjustedWilcoxonp=.2560. Do not conflate interval and multiplicity-adjusted test. Product-minus-MDAdditive+.00989 CI[-.00100,.02082],p=.2560. Independently calibrated pipeline comparison is not causaloperatorisolation. Productfalse-destinationrate16.49%; zero fake absorption is not fake rejection. |
| 17 | `paper/main.tex:593–618`; `thucnghiem/results/rq1_results/protocol.json` | Seven fixedconditions: control,GPS100m/GPS300m,time15min/time60min,copies2x/copies5x. Fivefixedmethods,40runs=1,400fits. Noise levels are designed stresses, not estimates of field error. Copies2x slightly increase graphARI,5x collapse means to~.30; no monotonic benefit/collapse-threshold claim. Product5x meanchange-.6108 CI[-.6318,-.5881]. Map scenario GIF is not streaming dynamics or a new benchmark. Primary and independentrerun remain unpooled. |
| 18 | `paper/main.tex:620–677` | Revisedcopydrift0for2x/5x/10x; legacy.0026/.0086/.0148. Coordinatedhigh-confidence reviseddrift.1688,legacy.0309; false-prioritylift.8828. Revised-minus-legacydrift.1379,Holmp~9.1e-12. More sensitivity under some low-confidenceE/N/Vinflation must not be hidden. |
| 19 | `paper/main.tex:650–677` | RevisedNDCG@5.6669 CI[.6306,.7018]; population-only.6709; random.6763. Revised-minus-legacy+.0121 notsignificantafterHolm. Do not conclude random significantlybetter. Spearman-.0304 CI[-.1165,.0549]; top5overlap.285 CI[.2349,.3400]. Weakalignment persists underoracle grouping. |
| 20 | `paper/main.tex:679–708`; `thucnghiem/results/rq3_results/rq3_paired_comparisons_seed.csv` | Productpartition revised-minus-legacyharm+14.34147785,pHolm.5627134221; missrate-.01875=-1.875percentagepoints,p.2472569036. Revised-minus-nearestharm+69.88463928,p4.091609844e-5; missrate+.1770833333,p1.174528414e-6. All40seedpairs. Manuscript approximates nearestdeadlinep as1.3e-6; CSVexactp differs slightly but conclusionunchanged. Per-resource figuredescriptive; no extraindependentpoints. Nearest-first superiority is conditional on simulation, not field endorsement. |
| 21–23 | `paper/main.tex:756–800` | No sourceauthenticity, fieldbenefit, policyvalidity, OODtransfer or deploymentreadiness claim. Localstability of constants coexists with weakalignment. Futurework is proposed, not completed. Releasev1.0.1 and laterstress additions need separatepins. |

## Citation checks and source identity

`references.json` contains12ordered entries, with [1]–[6] forslide24 and [7]–[12] forslide25. Every entry has a recommended content-slide citation and a human-readable shortentry. All12numbers occur in the speaker notes. Their grouping is thematic, not a claim that the order follows IEEE firstappearance.

- Louvain: primary arXiv author record confirms title, fourauthors, 2008 journalreference and journalDOI.
- Bilateralfiltering: authorpaper HTML/PDF available. IEEE DOIredirects to document710815 but requiresJavaScript. It is precedent for spatial-range products, not a claim that the whole graph formula is priorwork.
- ARI: Springer publisher record confirms title, authors, volume2,pages193–218,1985 and DOI.
- NDCG: Tampere authorinstitution record confirms Järvelin&Kekäläinen2002,ACMTOIS20(4),422–446,DOI. This source is a proposed presentation reference absent from original`references.bib`; manuscriptfile unchanged. Current implementation interpretation additionally checked against scikit-learnofficial docs and notebookcall.
- Humanitarianobjectives: publishersearchrecord and MITlabpublicationlist agree on Gralla,Goentzel,Fine2014. Earlyonline2013 does not invalidate the2014issuecitation.
- Socialsensing: officialWWW2010conferencePDF confirms identity; directACMpage403. DOIidentity corroborated bysearchmetadata, not falsely claimed as a successful pageopening.
- CrisisMMD: publisherCDNfullpaper and authorarXivrecord confirm identity. AAAIlandingpagebotblocked; DOIhaspublisherarticleid14983. A mistakenlytested14999page concerns a different work and was discarded, not used.
- FloodNet: author-ownedBinaLabGitHubrepository contains exactarticleBibTeX; authorarXivrecord describes UAVpost-Harveysceneunderstanding. ORNLinstitutionalrecord confirms2021journalmetadata and DOI. Earlier2020arXiv date is not publicationyearconflict.
- EMSR848: officialactivationpage exists but is JavaScript-driven. OfficialCopernicusnewsrecord names FloodinCentralVietNam and EMSR848. No mapproduct was downloaded or misidentified as studydata.
- OSM: officialcopyrightpage confirmsmapdata scope and ODbLattribution. It does not prove a particularhistoricalextract checksum or rowlineage.
- WorldPop: officialcatalogid56514 confirms2025constrainedpopulationcells,approximately100m,R2024Bv1,andDOIWP00803. Theproductiondate2024-12-01 is distinct from the2025populationtargetyear. DirectDOIbrowseropening unavailable; primarycatalogmetadataverified.
- Studyartifact: officialauthorGitHubv1.0.1releaseverified. TheZenodoDOIfromcurrentpaper/localmetadata could not beopened; it is retained inresearchmetadata as a reportedidentifier, notindependentlyresolved. Prefer theverifiedGitHubreleaseURL ontheaudienceslide. Therelease doesnotincludelaterfixedstressadditions.

No automatedRetractionWatchscreen, externalmodelreview, publicationapproval or human-readattestation is claimed.

## Speaking notes and language

- `speaker-notes.json`: exactly26objects, each with slide,title,seconds,notes; total1,175seconds(~19.6minutes) and2,541words beforequestions. Timingis anallocation,notameasuredrehearsal.
- `speaker-notes.md`: sameEnglishtextforhumanediting.
- No sources were replaced with generic disaster photographs. Generated diagrams and pedagogicalGIFs should be labeled as schematics or datasetvisualizations as appropriate.

## AI assistance record

Codex assisted with slide adaptation, English talk-track drafting, source checking and asset preparation. Scientific claims and numerical results are attributed to the supplied manuscript/artifacts; no new scientific validation is implied. This is a local preparation record, not a venue-specific AI-policy certification.
