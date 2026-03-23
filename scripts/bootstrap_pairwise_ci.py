#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from sklearn.metrics import average_precision_score


COMPARISONS = {
    "unseen_drug_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed1.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed0.json",
            "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed1.json",
            "results/recent_dtilm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_dtilm_seed2.json",
        ],
    },
    "unseen_drug_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed1.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed0.json",
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed1.json",
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed2.json",
        ],
    },
    "unseen_drug_base_vs_rf": {
        "a_name": "base",
        "b_name": "RF",
        "a_paths": [
            "results/full_base/BindingDB_Kd_unseen_drug_base_seed0.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed1.json",
            "results/multiseed_unseen_drug_base/BindingDB_Kd_unseen_drug_base_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_Kd_unseen_drug_rf_seed0.json",
            "results/rf_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_rf_seed1.json",
            "results/rf_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_rf_seed2.json",
        ],
    },
    "unseen_drug_hyperpcm_vs_rf": {
        "a_name": "HyperPCM",
        "b_name": "RF",
        "a_paths": [
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed0.json",
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed1.json",
            "results/recent_hyperpcm_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_hyperpcm_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_Kd_unseen_drug_rf_seed0.json",
            "results/rf_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_rf_seed1.json",
            "results/rf_unseen_drug_multiseed/BindingDB_Kd_unseen_drug_rf_seed2.json",
        ],
    },
    "blind_start_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_Kd_blind_start_dtilm_seed0.json",
            "results/recent_dtilm_blind_multiseed/BindingDB_Kd_blind_start_dtilm_seed1.json",
            "results/recent_dtilm_blind_multiseed/BindingDB_Kd_blind_start_dtilm_seed2.json",
        ],
    },
    "blind_start_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_Kd_blind_start_hyperpcm_seed0.json",
            "results/recent_hyperpcm_blind_multiseed/BindingDB_Kd_blind_start_hyperpcm_seed1.json",
            "results/recent_hyperpcm_blind_multiseed/BindingDB_Kd_blind_start_hyperpcm_seed2.json",
        ],
    },
    "blind_start_base_vs_rf": {
        "a_name": "base",
        "b_name": "RF",
        "a_paths": [
            "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_Kd_blind_start_rf_seed0.json",
            "results/rf_blind_multiseed/BindingDB_Kd_blind_start_rf_seed1.json",
            "results/rf_blind_multiseed/BindingDB_Kd_blind_start_rf_seed2.json",
        ],
    },
    "blind_start_raicd_vs_base": {
        "a_name": "base",
        "b_name": "RAICD",
        "a_paths": [
            "results/full_blind_base/BindingDB_Kd_blind_start_base_seed0.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed1.json",
            "results/multiseed_blind_base/BindingDB_Kd_blind_start_base_seed2.json",
        ],
        "b_paths": [
            "results/full_blind_raicd_simattn/BindingDB_Kd_blind_start_raicd_seed0.json",
            "results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed1_both.json",
            "results/multiseed_blind_raicd/BindingDB_Kd_blind_start_raicd_seed2_both.json",
        ],
    },
    "patent_base_vs_raicd": {
        "a_name": "base",
        "b_name": "RAICD",
        "a_paths": [
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed0_both.json",
            "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed1_both.json",
            "results/full_bindingdb_patent_raicd/BindingDB_patent_patent_temporal_raicd_seed2_both.json",
        ],
    },
    "patent_base_vs_ftm": {
        "a_name": "base",
        "b_name": "FTM",
        "a_paths": [
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed0_chem32_top4_shr8p0.json",
            "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed1_chem32_top4_shr8p0.json",
            "results/full_bindingdb_patent_ftm/BindingDB_patent_patent_temporal_ftm_seed2_chem32_top4_shr8p0.json",
        ],
    },
    "patent_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_patent_patent_temporal_dtilm_seed0.json",
            "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed1.json",
            "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed2.json",
        ],
    },
    "patent_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_patent_patent_temporal_hyperpcm_seed0.json",
            "results/recent_hyperpcm_patent_multiseed/BindingDB_patent_patent_temporal_hyperpcm_seed1.json",
            "results/recent_hyperpcm_patent_multiseed/BindingDB_patent_patent_temporal_hyperpcm_seed2.json",
        ],
    },
    "patent_base_vs_rf": {
        "a_name": "base",
        "b_name": "RF",
        "a_paths": [
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed0.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed1.json",
            "results/full_bindingdb_patent_base/BindingDB_patent_patent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_patent_patent_temporal_rf_seed0.json",
            "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed1.json",
            "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed2.json",
        ],
    },
    "patent_dtilm_vs_rf": {
        "a_name": "DTI-LM",
        "b_name": "RF",
        "a_paths": [
            "results/recent_panel_stage1/BindingDB_patent_patent_temporal_dtilm_seed0.json",
            "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed1.json",
            "results/recent_dtilm_patent_multiseed/BindingDB_patent_patent_temporal_dtilm_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_patent_patent_temporal_rf_seed0.json",
            "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed1.json",
            "results/rf_patent_multiseed/BindingDB_patent_patent_temporal_rf_seed2.json",
        ],
    },
    "nonpatent_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed0.json",
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed1.json",
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed0.json",
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed1.json",
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed2.json",
        ],
    },
    "nonpatent_base_vs_rf": {
        "a_name": "base",
        "b_name": "RF",
        "a_paths": [
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed0.json",
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed1.json",
            "results/full_bindingdb_nonpatent_temporal_base/BindingDB_nonpatent_Kd_nonpatent_temporal_base_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed0.json",
            "results/rf_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed1.json",
            "results/rf_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed2.json",
        ],
    },
    "nonpatent_dtilm_vs_rf": {
        "a_name": "DTI-LM",
        "b_name": "RF",
        "a_paths": [
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed0.json",
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed1.json",
            "results/recent_bindingdb_nonpatent_temporal_dtilm/BindingDB_nonpatent_Kd_nonpatent_temporal_dtilm_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed0.json",
            "results/rf_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed1.json",
            "results/rf_nonpatent_multiseed/BindingDB_nonpatent_Kd_nonpatent_temporal_rf_seed2.json",
        ],
    },
    "scaffold_drug_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_bindingdb_kd_scaffold_base/BindingDB_Kd_scaffold_drug_base_seed0.json",
            "results/full_bindingdb_kd_scaffold_base/BindingDB_Kd_scaffold_drug_base_seed1.json",
            "results/full_bindingdb_kd_scaffold_base/BindingDB_Kd_scaffold_drug_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_bindingdb_kd_scaffold_hyperpcm/BindingDB_Kd_scaffold_drug_hyperpcm_seed0.json",
            "results/recent_bindingdb_kd_scaffold_hyperpcm/BindingDB_Kd_scaffold_drug_hyperpcm_seed1.json",
            "results/recent_bindingdb_kd_scaffold_hyperpcm/BindingDB_Kd_scaffold_drug_hyperpcm_seed2.json",
        ],
    },
    "kd_unseen_target_base_vs_ftm": {
        "a_name": "base",
        "b_name": "FTM",
        "a_paths": [
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
            "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed1_chem32_top4_shr8p0.json",
            "results/full_ftm_unseen_target_sparse_multiseed/BindingDB_Kd_unseen_target_ftm_seed2_chem32_top4_shr8p0.json",
        ],
    },
    "kd_unseen_target_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_Kd_unseen_target_dtilm_seed0.json",
            "results/recent_dtilm_unseen_target_multiseed/BindingDB_Kd_unseen_target_dtilm_seed1.json",
            "results/recent_dtilm_unseen_target_multiseed/BindingDB_Kd_unseen_target_dtilm_seed2.json",
        ],
    },
    "kd_unseen_target_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_panel_stage1/BindingDB_Kd_unseen_target_hyperpcm_seed0.json",
            "results/recent_hyperpcm_unseen_target_multiseed/BindingDB_Kd_unseen_target_hyperpcm_seed1.json",
            "results/recent_hyperpcm_unseen_target_multiseed/BindingDB_Kd_unseen_target_hyperpcm_seed2.json",
        ],
    },
    "kd_unseen_target_base_vs_rf": {
        "a_name": "base",
        "b_name": "RF",
        "a_paths": [
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed0.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed1.json",
            "results/full_unseen_target_base_multiseed/BindingDB_Kd_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/rf_panel_stage1/BindingDB_Kd_unseen_target_rf_seed0.json",
            "results/rf_unseen_target_multiseed/BindingDB_Kd_unseen_target_rf_seed1.json",
            "results/rf_unseen_target_multiseed/BindingDB_Kd_unseen_target_rf_seed2.json",
        ],
    },
    "ki_base_vs_raicd": {
        "a_name": "base",
        "b_name": "RAICD",
        "a_paths": [
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed0.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed1.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/full_bindingdb_ki_unseen_target_raicd_multiseed/BindingDB_Ki_unseen_target_raicd_seed0_both.json",
            "results/full_bindingdb_ki_unseen_target_raicd_multiseed/BindingDB_Ki_unseen_target_raicd_seed1_both.json",
            "results/full_bindingdb_ki_unseen_target_raicd_multiseed/BindingDB_Ki_unseen_target_raicd_seed2_both.json",
        ],
    },
    "ki_base_vs_ftm": {
        "a_name": "base",
        "b_name": "FTM",
        "a_paths": [
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed0.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed1.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/full_bindingdb_ki_unseen_target_ftm_multiseed/BindingDB_Ki_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
            "results/full_bindingdb_ki_unseen_target_ftm_multiseed/BindingDB_Ki_unseen_target_ftm_seed1_chem32_top4_shr8p0.json",
            "results/full_bindingdb_ki_unseen_target_ftm_multiseed/BindingDB_Ki_unseen_target_ftm_seed2_chem32_top4_shr8p0.json",
        ],
    },
    "ki_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed0.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed1.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed0.json",
            "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed1.json",
            "results/recent_dtilm_ki_multiseed/BindingDB_Ki_unseen_target_dtilm_seed2.json",
        ],
    },
    "ki_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed0.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed1.json",
            "results/full_bindingdb_ki_unseen_target_base_multiseed/BindingDB_Ki_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed0.json",
            "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed1.json",
            "results/recent_hyperpcm_ki_multiseed/BindingDB_Ki_unseen_target_hyperpcm_seed2.json",
        ],
    },
    "davis_base_vs_raicd": {
        "a_name": "base",
        "b_name": "RAICD",
        "a_paths": [
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed0.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed1.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/full_davis_unseen_target_raicd_multiseed/DAVIS_unseen_target_raicd_seed0_both.json",
            "results/full_davis_unseen_target_raicd_multiseed/DAVIS_unseen_target_raicd_seed1_both.json",
            "results/full_davis_unseen_target_raicd_multiseed/DAVIS_unseen_target_raicd_seed2_both.json",
        ],
    },
    "davis_base_vs_dtilm": {
        "a_name": "base",
        "b_name": "DTI-LM",
        "a_paths": [
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed0.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed1.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed0.json",
            "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed1.json",
            "results/recent_dtilm_davis_multiseed/DAVIS_unseen_target_dtilm_seed2.json",
        ],
    },
    "davis_base_vs_hyperpcm": {
        "a_name": "base",
        "b_name": "HyperPCM",
        "a_paths": [
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed0.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed1.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed0.json",
            "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed1.json",
            "results/recent_hyperpcm_davis_multiseed/DAVIS_unseen_target_hyperpcm_seed2.json",
        ],
    },
    "davis_base_vs_ftm": {
        "a_name": "base",
        "b_name": "FTM",
        "a_paths": [
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed0.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed1.json",
            "results/full_davis_unseen_target_base_multiseed/DAVIS_unseen_target_base_seed2.json",
        ],
        "b_paths": [
            "results/full_davis_unseen_target_ftm_multiseed/DAVIS_unseen_target_ftm_seed0_chem32_top4_shr8p0.json",
            "results/full_davis_unseen_target_ftm_multiseed/DAVIS_unseen_target_ftm_seed1_chem32_top4_shr8p0.json",
            "results/full_davis_unseen_target_ftm_multiseed/DAVIS_unseen_target_ftm_seed2_chem32_top4_shr8p0.json",
        ],
    },
}


def load_preds(path: Path) -> tuple[list[int], list[float], float]:
    with path.open() as fh:
        data = json.load(fh)
    labels = [int(x) for x in data["test_predictions"]["labels"]]
    probs = [float(x) for x in data["test_predictions"]["probabilities"]]
    auprc = float(data["test_metrics"]["auprc"])
    return labels, probs, auprc


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("empty list")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def bootstrap_mean_delta(
    a_seed_data: list[tuple[list[int], list[float], float]],
    b_seed_data: list[tuple[list[int], list[float], float]],
    num_bootstrap: int,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    observed_deltas = []
    for (_, _, a_auprc), (_, _, b_auprc) in zip(a_seed_data, b_seed_data):
        observed_deltas.append(b_auprc - a_auprc)
    observed_mean = statistics.mean(observed_deltas)

    boot_means: list[float] = []
    for _ in range(num_bootstrap):
        seed_deltas = []
        for (labels_a, probs_a, _), (labels_b, probs_b, _) in zip(a_seed_data, b_seed_data):
            if labels_a != labels_b:
                raise ValueError("label mismatch between paired runs")
            n = len(labels_a)
            indices = [rng.randrange(n) for _ in range(n)]
            sample_labels = [labels_a[i] for i in indices]
            sample_probs_a = [probs_a[i] for i in indices]
            sample_probs_b = [probs_b[i] for i in indices]
            delta = average_precision_score(sample_labels, sample_probs_b) - average_precision_score(sample_labels, sample_probs_a)
            seed_deltas.append(float(delta))
        boot_means.append(statistics.mean(seed_deltas))
    boot_means.sort()
    ci_low = percentile(boot_means, 0.025)
    ci_high = percentile(boot_means, 0.975)
    prob_positive = sum(value > 0 for value in boot_means) / len(boot_means)
    return {
        "observed_seed_deltas": observed_deltas,
        "observed_mean_delta": observed_mean,
        "ci95": [ci_low, ci_high],
        "prob_delta_gt_0": prob_positive,
        "num_bootstrap": num_bootstrap,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    results = {}
    selected = set(args.only) if args.only else set(COMPARISONS.keys())
    for name, spec in COMPARISONS.items():
        if name not in selected:
            continue
        a_seed_data = [load_preds(Path(path)) for path in spec["a_paths"] if Path(path).exists()]
        b_seed_data = [load_preds(Path(path)) for path in spec["b_paths"] if Path(path).exists()]
        if len(a_seed_data) != len(spec["a_paths"]) or len(b_seed_data) != len(spec["b_paths"]):
            results[name] = {"status": "incomplete"}
            continue
        stats = bootstrap_mean_delta(a_seed_data, b_seed_data, args.num_bootstrap, args.seed)
        results[name] = {
            "status": "done",
            "a_name": spec["a_name"],
            "b_name": spec["b_name"],
            **stats,
        }

    if args.output:
        args.output.write_text(json.dumps(results, indent=2))
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
