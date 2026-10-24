# Scientific research controls

Freeze hypothesis, universe selection, source/adjustment, date split, costs and metric definitions before evaluation. The fixed example suite retains all eight attempted configurations and a failed control; it does not select the best curve. FIXTURE results measure software behavior only.

`chronological_split` partitions train/validation/holdout without random shuffling. Purging removes overlapping-label boundaries and embargo reserves additional sessions; choose horizons explicitly. `walk_forward_folds` produces expanding or rolling historical folds; OOS remains historical and cannot certify an untouched prospective period. `fit_standardizer` fits mean/scale only on training indices. Extreme finite inputs that overflow calculations fail closed.

HoldoutAudit writes unique append-only local review events. Repeated review is visible; using results to tune permanently contaminates overlapping sessions with the same dataset hash, even if a smaller subinterval is renamed. Local files cannot prove that nobody viewed a holdout elsewhere. New dataset hashes/revisions require human contamination review. The runner's PREDECLARED_HOLDOUT records declared fixed-rule evaluation, never automatic independent-validation certification.

Circular fixed-block bootstrap estimates uncertainty of a historical mean under approximate stationary short-memory dependence. Block length/resamples/seed are recorded; intervals are sensitive to choices and do not adjust for repeated strategy selection. DSR, PBO and White's Reality Check are Planned, not copied unverified formulas.

Candidate ranking accepts explicit bounded dimension inputs with configurable disclosed weights. Missing required dimensions produce INSUFFICIENT_EVIDENCE and null score. The default weights emphasize data reliability, OOS stability, execution feasibility and cost robustness over raw performance; they are research priorities, not calibrated probabilities. The platform does not invent absent dimension scores from a backtest.

Evidence grades: Exploratory, Backtested, Out-of-Sample Validated, Paper-Monitored, Research Candidate. This milestone's experiment runner remains **Exploratory** and never promotes automatically. Deterministic critic reports Evidence/Inference/Hypothesis/Uncertainty/Actionable Research Question, synthetic-only flags, zero-cost controls and missing holdout limitations. Full model-driven planning/tool orchestration remains partial; the core works without LLM access.
