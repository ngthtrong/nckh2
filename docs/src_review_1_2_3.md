
Review 1
Overall evaluation
1: weak accept
This study addresses an important problem in flood-rescue decision support by developing a pipeline that integrates report clustering, duplicate-aware priority ranking, and dispatch simulation. The study is particularly valuable because it examines how errors in clustering and ranking can propagate to downstream rescue decisions.
However, there are some points need to be clarified:
1.The proposed product-gated clustering and priority score do not consistently outperform the baseline methods. Please clarify the specific advantage and practical value of the proposed approach.
2.The experimental design is systematic, but the study relies on synthetic data. Please explain more clearly how the generated data and scenarios represent realistic flood-rescue situations.
3.Please provide additional experiments to better evaluate the robustness and limitations of the proposed framework.
Several minor points includings:
-The manuscript uses terms such as “product Louvain,” “product Leiden,” “additive Louvain,” and “matched-density additive.” A brief explanation of these terms at their first occurrence would improve readability.
-The manuscript includes several clustering and ranking baselines, but the reasons for selecting these particular methods are not always clear.
Review 2
Overall evaluation
2: accept
Strengths
1.Methodological Rigor & Auditability: The paper avoids false optimism by auditing a fail-closed pipeline with evaluator-only ground truth joined after scheduling decisions.
2.Honest Reporting of Negative Results: The paper candidly admits that sophisticated scoring and clustering failed to beat random baselines or simple heuristics like nearest-first dispatch.
3.Identification of Vulnerabilities: Highlighting that "coordinated high-confidence campaigns" remain a critical vulnerability provides valuable security awareness for disaster-response applications.

Critical Limitations & Weaknesses

1.Poor Downstream Alignment: High clustering accuracy did not translate to effective priority scoring or resource dispatch, exposing a disconnect between proxy metrics (ARI) and operational utility.
2.No Field Readiness: As the authors state, the system does not prove misinformation robustness, policy validity, or field readiness.
Review 3
Overall evaluation
1: weak accept
The paper addresses an important flood-rescue decision-support problem by integrating clustering, priority ranking, and dispatch simulation. However, several issues need to be addressed:

* The proposed methods do not consistently outperform the baselines. The authors should clarify their specific advantages and practical value.
* The evaluation relies on synthetic data; the authors should better justify its realism and representativeness of actual flood-rescue scenarios.
* Additional experiments are needed to assess robustness and limitations under noise, duplication, and varying operational conditions.
* High clustering accuracy (ARI) does not necessarily improve priority ranking or dispatch, indicating poor downstream alignment between proxy metrics and operational utility.
* The framework does not yet demonstrate robustness to misinformation, policy constraints, or real-world field deployment.
* Terms such as “product Louvain/Leiden” and “additive Louvain” should be briefly explained, and the rationale for selecting the baselines should be clarified.

Overall, the topic is relevant, but the practical superiority and field readiness of the proposed framework are not yet sufficiently demonstrated.
