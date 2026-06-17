"""Train only M5 (Short Horizon Regressor) - Others already trained."""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_training_config, load_model_config
from src.data.loader import load_raw_data, time_based_split, create_groups, dataset_model
from src.models.m5_short_horizon import M5Trainer

print("="*80)
print("TRAINING M5 (SHORT HORIZON REGRESSOR)")
print("="*80)

# Load config
train_cfg = load_training_config()
m5_cfg = load_model_config("m5")
registry_dir = train_cfg['registry']['model_dir']

# Load data
df = load_raw_data(train_cfg['data']['raw_path'])
groups = create_groups(df)

# Prepare M4 dataset first (to get the right subset)
m4_cfg = load_model_config("m4")
df_m4 = dataset_model(df, m4_cfg['drop_columns'])
df_m4 = df_m4[df_m4['LapsUntilNextPit'] != 1]  # Exclude pit laps

# Load M3 OOF predictions
oof3 = np.load(f"{registry_dir}/m3_oof_pitprobin3.npy")
print(f"✓ Loaded M3 OOF predictions: {len(oof3)} samples")

# Get M3 train indices (need to reconstruct to match OOF)
m3_cfg = load_model_config("m3")
df_m3 = dataset_model(df, m3_cfg['drop_columns']).copy()
df_m3['WillPitWithin3Laps'] = df_m3['LapsUntilNextPit'].between(1, 3).astype(int)
X_3 = df_m3.drop(columns=['LapsUntilNextPit', 'WillPitWithin3Laps'])
y_3 = df_m3['WillPitWithin3Laps']
groups_3 = create_groups(df_m3)
splits_m3 = time_based_split(df_m3, X_3, y_3, groups_3,
                              train_cfg['data']['train_end_year'],
                              train_cfg['data']['valid_year'],
                              train_cfg['data']['test_year'])

# Generate pit-in-3 probs for valid/test using saved M3 model
import joblib
m3_pipeline = joblib.load(f"{registry_dir}/m3_pipeline.pkl")
print("✓ Loaded M3 pipeline")

# Need to add PitProb to valid/test for M3 inference
m2_oof = np.load(f"{registry_dir}/m2_oof_pitprob.npy")
m2_pipeline = joblib.load(f"{registry_dir}/m2_pipeline.pkl")

# Generate valid/test pit probs
m2_cfg = load_model_config("m2")
df_m2 = dataset_model(df, m2_cfg['drop_columns'])
X_2 = df_m2.drop(columns=[m2_cfg['target']])
y_2 = df_m2[m2_cfg['target']]
splits_m2 = time_based_split(df_m2, X_2, y_2, groups,
                              train_cfg['data']['train_end_year'],
                              train_cfg['data']['valid_year'],
                              train_cfg['data']['test_year'])

valid_pit_prob = m2_pipeline.predict_proba(splits_m2['X_valid'])[:, 1]
test_pit_prob = m2_pipeline.predict_proba(splits_m2['X_test'])[:, 1]

# Now generate pit-in-3 probs
splits_m3['X_valid']['PitProb'] = pd.Series(valid_pit_prob, index=splits_m2['X_valid'].index).reindex(splits_m3['X_valid'].index)
splits_m3['X_test']['PitProb'] = pd.Series(test_pit_prob, index=splits_m2['X_test'].index).reindex(splits_m3['X_test'].index)

valid_pit_prob_in3 = m3_pipeline.predict_proba(splits_m3['X_valid'])[:, 1]
test_pit_prob_in3 = m3_pipeline.predict_proba(splits_m3['X_test'])[:, 1]

# Create OOF series
oof3_s = pd.Series(oof3, index=splits_m3['X_train'].index)
valid3_s = pd.Series(valid_pit_prob_in3, index=splits_m3['X_valid'].index)
test3_s = pd.Series(test_pit_prob_in3, index=splits_m3['X_test'].index)

print("✓ Generated all meta-features")

# Now prepare M5
df_m5 = df_m4[df_m4['LapsUntilNextPit'] <= 10].copy()
X_5 = df_m5.drop(columns=['LapsUntilNextPit'])
y_5 = df_m5['LapsUntilNextPit']
groups_m5 = create_groups(df_m5)
splits_m5 = time_based_split(df_m5, X_5, y_5, groups_m5,
                              train_cfg['data']['train_end_year'],
                              train_cfg['data']['valid_year'],
                              train_cfg['data']['test_year'])

# Attach PitProbIn3
splits_m5['X_train']['PitProbIn3'] = oof3_s.reindex(splits_m5['X_train'].index)
splits_m5['X_valid']['PitProbIn3'] = valid3_s.reindex(splits_m5['X_valid'].index)
splits_m5['X_test']['PitProbIn3'] = test3_s.reindex(splits_m5['X_test'].index)

print(f"✓ M5 dataset: {len(df_m5)} samples")
print(f"  Train: {len(splits_m5['X_train'])}")
print(f"  Valid: {len(splits_m5['X_valid'])}")
print(f"  Test: {len(splits_m5['X_test'])}")

# Train M5
m5 = M5Trainer(m5_cfg, train_cfg['mlflow']['tracking_uri'])
m5.setup_mlflow(train_cfg['mlflow']['experiment_name'])

m5.optimize_hyperparameters(
    splits_m5['X_train'], splits_m5['y_train'],
    splits_m5['X_valid'], splits_m5['y_valid'],
    n_trials=m5_cfg.get('optuna_trials', 50)
)

# Train with 3× sample weights
X_m5_final = X_5[df_m5["Split"] != "test"].copy()
y_m5_final = y_5[df_m5["Split"] != "test"]
X_m5_final['PitProbIn3'] = pd.concat([oof3_s, valid3_s]).reindex(X_m5_final.index)
m5.train(X_m5_final, y_m5_final, apply_sample_weights=True)

# Evaluate on test
metrics_m5 = m5.evaluate(splits_m5['X_test'], splits_m5['y_test'])
m5.log_to_mlflow(metrics_m5, m5.best_params)
m5.save(f"{registry_dir}/m5_pipeline.pkl")

print("\n" + "="*80)
print("✅ M5 TRAINING COMPLETE!")
print("="*80)
print("\n✅ All 5 models are now trained and saved:")
print(f"   • M1: {registry_dir}/m1_pipeline.pkl")
print(f"   • M2: {registry_dir}/m2_pipeline.pkl")
print(f"   • M3: {registry_dir}/m3_pipeline.pkl")
print(f"   • M4: {registry_dir}/m4_pipeline.pkl")
print(f"   • M5: {registry_dir}/m5_pipeline.pkl")
