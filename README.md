# Coverage QoE score: evaluation on public drive-test data

Code for the evaluation in Section 4 of:

M. Babachekh, A. Bahri, A. Bengag, F. Bouhafer, *A Multi-KPI Coverage Score for Mobile Networks: Design and Evaluation on Public LTE Drive-Test Data*.

## Setup

```bash
pip install -r requirements.txt
```

Run with Python 3.12. Package versions are pinned to those used for the paper.

## Data

4G LTE drive-test dataset of Raca et al. (ACM MMSys 2018), CC BY 4.0.

1. Download `LTE_Dataset.zip` from https://zenodo.org/records/1219679
2. Unzip it into `data/raw/d3_lte_ucc/` (this gives `Dataset/<mobility>/*.csv`)

The notebook keeps LTE samples taken during an active download with all values present (107,577), then removes those with a reported distance to the serving cell above 20 km (4,592) and those with RSRP (55) or RSRQ (611) outside the 3GPP reporting ranges. Some samples fail more than one test; 5,194 are removed in all, leaving 102,383.

## Run

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/05_coverage_qoe_d3.ipynb
```

| Output | Paper |
|---|---|
| `results/tab_d3_coverage_results.csv` | Table 2, single split (seed 42) with bootstrap intervals |
| `results/tab_d3_repeated_splits.csv`, `tab_d3_repeated_splits_summary.csv` | Table 2, 30 splits (fixed scores, variants, learned references); Fig. 1 |
| `results/tab_d3_sensitivity.csv` | Table 2, single-split column for the variants (middle part) |
| `results/tab_d3_robustness.csv` | Sect. 4.2: score with penalties; larger sample without the distance requirement |
| `results/tab_d3_weights.csv` | Weight procedure applied to the training traces (Sect. 4.2) |
| `results/tab_d3_bands_all.csv` | Band shares and medians (Sect. 4.3); Fig. 2 |
| `results/figures/d3_repeated_splits.pdf`, `d3_throughput_by_band.pdf` | Figs. 1 and 2 |

The scoring functions are in `src/qoe_framework.py`. The six service scores that the paper omits for space, with all levels, weights and penalties, are in `SERVICE_SCORES.md`.

## Licence

Code: MIT (see `LICENSE`). The dataset is published separately by its authors under CC BY 4.0.
