"""
F1 Strategy Engine Training Pipeline
Orchestrates training of all 5 models: M1 → M2 → M3 → M4 → M5
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_training_config, load_model_config
from src.data.loader import load_raw_data, time_based_split, create_groups, dataset_model
from src.models.m1_lap_time import M1Trainer
from src.models.m2_pit_lap import M2Trainer
from src.models.m3_pit_in_3 import M3Trainer
from src.models.m4_long_horizon import M4Trainer
from src.models.m5_short_horizon import M5Trainer


def main():
    """Main training pipeline."""
    print("=" * 80)
    print("F1 STRATEGY ENGINE - TRAINING PIPELINE")
    print("=" * 80)

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. Load Configuration
    # ═══════════════════════════════════════════════════════════════════════════
    train_cfg = load_training_config()
    print(f"\n✓ Loaded training config")
    print(f"  Train: ≤{train_cfg['data']['train_end_year']}")
    print(f"  Valid: {train_cfg['data']['valid_year']}")
    print(f"  Test:  {train_cfg['data']['test_year']}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. Load & Enrich Data
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*80}")
    print("LOADING DATA")
    print(f"{'─'*80}")

    # Load enriched dataset (already has all rolling features)
    df = load_raw_data(train_cfg['data']['raw_path'])
    print(f"✓ Loaded enriched dataset: {df.shape}")
    print(f"✓ Columns: {len(df.columns)}")

    # Create race-level groups for GroupKFold
    groups = create_groups(df)
    print(f"✓ Created {groups.nunique()} race groups")

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. Train M1 (Lap Time Regressor) - Independent
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("MODEL 1: LAP TIME REGRESSOR")
    print(f"{'='*80}")

    m1_cfg = load_model_config("m1")
    df_m1 = dataset_model(df, m1_cfg['drop_columns'])

    X_1 = df_m1.drop(columns=[m1_cfg['target']])
    y_1 = df_m1[m1_cfg['target']]
    splits_m1 = time_based_split(df_m1, X_1, y_1, groups,
                                  train_cfg['data']['train_end_year'],
                                  train_cfg['data']['valid_year'],
                                  train_cfg['data']['test_year'])

    m1 = M1Trainer(m1_cfg, train_cfg['mlflow']['tracking_uri'])
    m1.setup_mlflow(train_cfg['mlflow']['experiment_name'])

    m1.optimize_hyperparameters(
        splits_m1['X_train'], splits_m1['y_train'],
        splits_m1['X_valid'], splits_m1['y_valid'],
        n_trials=m1_cfg.get('optuna_trials', 50)
    )

    # Train on train+valid
    X_m1_final = X_1[df_m1["Year"] <= train_cfg['data']['valid_year']]
    y_m1_final = y_1[df_m1["Year"] <= train_cfg['data']['valid_year']]
    m1.train(X_m1_final, y_m1_final)

    # Evaluate on test
    metrics_m1 = m1.evaluate(splits_m1['X_test'], splits_m1['y_test'])
    m1.log_to_mlflow(metrics_m1, m1.best_params)

    # Save model
    registry_dir = train_cfg['registry']['model_dir']
    Path(registry_dir).mkdir(parents=True, exist_ok=True)
    m1.save(f"{registry_dir}/m1_pipeline.pkl")

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. Train M2 (Pit Lap Classifier) → Generate OOF for M3/M4
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("MODEL 2: PIT LAP CLASSIFIER")
    print(f"{'='*80}")

    m2_cfg = load_model_config("m2")
    df_m2 = dataset_model(df, m2_cfg['drop_columns'])

    X_2 = df_m2.drop(columns=[m2_cfg['target']])
    y_2 = df_m2[m2_cfg['target']]
    splits_m2 = time_based_split(df_m2, X_2, y_2, groups,
                                  train_cfg['data']['train_end_year'],
                                  train_cfg['data']['valid_year'],
                                  train_cfg['data']['test_year'])

    m2 = M2Trainer(m2_cfg, train_cfg['mlflow']['tracking_uri'])
    m2.setup_mlflow(train_cfg['mlflow']['experiment_name'])

    m2.optimize_hyperparameters(
        splits_m2['X_train'], splits_m2['y_train'],
        splits_m2['X_valid'], splits_m2['y_valid'],
        n_trials=m2_cfg.get('optuna_trials', 50)
    )

    # Train on train only (for OOF)
    m2.train(splits_m2['X_train'], splits_m2['y_train'])

    # Generate OOF predictions on train set
    oof_pit_prob = m2.generate_oof_predictions(
        splits_m2['X_train'], splits_m2['y_train'], splits_m2['groups_train'],
        n_splits=train_cfg['data']['cv_folds']
    )

    # Retrain on train+valid for final model
    X_m2_final = X_2[df_m2["Year"] <= train_cfg['data']['valid_year']]
    y_m2_final = y_2[df_m2["Year"] <= train_cfg['data']['valid_year']]
    m2.train(X_m2_final, y_m2_final)

    # Evaluate on test
    metrics_m2 = m2.evaluate(splits_m2['X_test'], splits_m2['y_test'])
    m2.log_to_mlflow(metrics_m2, m2.best_params)

    # Save model + OOF
    m2.save(f"{registry_dir}/m2_pipeline.pkl")
    np.save(f"{registry_dir}/m2_oof_pitprob.npy", oof_pit_prob)
    print(f"✓ Saved OOF pit-probs: {len(oof_pit_prob)} samples")

    # Generate pit-probs for valid/test sets
    valid_pit_prob = m2.pipeline.predict_proba(splits_m2['X_valid'])[:, 1]
    test_pit_prob = m2.pipeline.predict_proba(splits_m2['X_test'])[:, 1]

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. Train M3 (Pit-in-3 Classifier) → Generate OOF for M4/M5
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("MODEL 3: PIT-IN-3 CLASSIFIER")
    print(f"{'='*80}")

    m3_cfg = load_model_config("m3")
    df_m3 = dataset_model(df, m3_cfg['drop_columns']).copy()

    # Create target
    df_m3['WillPitWithin3Laps'] = df_m3['LapsUntilNextPit'].between(1, 3).astype(int)

    X_3 = df_m3.drop(columns=['LapsUntilNextPit', 'WillPitWithin3Laps'])
    y_3 = df_m3['WillPitWithin3Laps']
    splits_m3 = time_based_split(df_m3, X_3, y_3, groups,
                                  train_cfg['data']['train_end_year'],
                                  train_cfg['data']['valid_year'],
                                  train_cfg['data']['test_year'])

    # Attach PitProb meta-feature (index-aligned)
    oof_s = pd.Series(oof_pit_prob, index=splits_m2['X_train'].index)
    valid_s = pd.Series(valid_pit_prob, index=splits_m2['X_valid'].index)
    test_s = pd.Series(test_pit_prob, index=splits_m2['X_test'].index)

    splits_m3['X_train']['PitProb'] = oof_s.reindex(splits_m3['X_train'].index)
    splits_m3['X_valid']['PitProb'] = valid_s.reindex(splits_m3['X_valid'].index)
    splits_m3['X_test']['PitProb'] = test_s.reindex(splits_m3['X_test'].index)
    print("✓ Attached PitProb meta-feature")

    m3 = M3Trainer(m3_cfg, train_cfg['mlflow']['tracking_uri'])
    m3.setup_mlflow(train_cfg['mlflow']['experiment_name'])

    m3.optimize_hyperparameters(
        splits_m3['X_train'], splits_m3['y_train'],
        splits_m3['X_valid'], splits_m3['y_valid'],
        n_trials=m3_cfg.get('optuna_trials', 50)
    )

    # Train on train only (for OOF)
    m3.train(splits_m3['X_train'], splits_m3['y_train'])

    # Generate OOF predictions
    oof_pit_prob_in3 = m3.generate_oof_predictions(
        splits_m3['X_train'], splits_m3['y_train'], splits_m3['groups_train'],
        n_splits=train_cfg['data']['cv_folds']
    )

    # Retrain on train+valid
    X_m3_final = X_3[df_m3["Year"] <= train_cfg['data']['valid_year']].copy()
    y_m3_final = y_3[df_m3["Year"] <= train_cfg['data']['valid_year']]
    X_m3_final['PitProb'] = pd.concat([oof_s, valid_s]).reindex(X_m3_final.index)
    m3.train(X_m3_final, y_m3_final)

    # Evaluate on test
    metrics_m3 = m3.evaluate(splits_m3['X_test'], splits_m3['y_test'])
    m3.log_to_mlflow(metrics_m3, m3.best_params)

    # Save model + OOF
    m3.save(f"{registry_dir}/m3_pipeline.pkl")
    np.save(f"{registry_dir}/m3_oof_pitprobin3.npy", oof_pit_prob_in3)

    # Generate pit-in-3 probs for valid/test
    valid_pit_prob_in3 = m3.pipeline.predict_proba(splits_m3['X_valid'])[:, 1]
    test_pit_prob_in3 = m3.pipeline.predict_proba(splits_m3['X_test'])[:, 1]

    # ═══════════════════════════════════════════════════════════════════════════
    # 6. Train M4 (Long Horizon Regressor)
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("MODEL 4: LONG HORIZON REGRESSOR")
    print(f"{'='*80}")

    m4_cfg = load_model_config("m4")
    df_m4 = dataset_model(df, m4_cfg['drop_columns'])
    df_m4 = df_m4[df_m4['LapsUntilNextPit'] != 1]  # Exclude pit laps

    X_4 = df_m4.drop(columns=['LapsUntilNextPit'])
    y_4 = df_m4['LapsUntilNextPit']
    groups_m4 = create_groups(df_m4)
    splits_m4 = time_based_split(df_m4, X_4, y_4, groups_m4,
                                  train_cfg['data']['train_end_year'],
                                  train_cfg['data']['valid_year'],
                                  train_cfg['data']['test_year'])

    # Attach PitProbIn3 meta-feature
    oof3_s = pd.Series(oof_pit_prob_in3, index=splits_m3['X_train'].index)
    valid3_s = pd.Series(valid_pit_prob_in3, index=splits_m3['X_valid'].index)
    test3_s = pd.Series(test_pit_prob_in3, index=splits_m3['X_test'].index)

    splits_m4['X_train']['PitProbIn3'] = oof3_s.reindex(splits_m4['X_train'].index)
    splits_m4['X_valid']['PitProbIn3'] = valid3_s.reindex(splits_m4['X_valid'].index)
    splits_m4['X_test']['PitProbIn3'] = test3_s.reindex(splits_m4['X_test'].index)
    print("✓ Attached PitProbIn3 meta-feature")

    m4 = M4Trainer(m4_cfg, train_cfg['mlflow']['tracking_uri'])
    m4.setup_mlflow(train_cfg['mlflow']['experiment_name'])

    m4.optimize_hyperparameters(
        splits_m4['X_train'], splits_m4['y_train'],
        splits_m4['X_valid'], splits_m4['y_valid'],
        n_trials=m4_cfg.get('optuna_trials', 50)
    )

    # Train on train+valid with log1p
    X_m4_final = X_4[df_m4["Year"] <= train_cfg['data']['valid_year']].copy()
    y_m4_final = y_4[df_m4["Year"] <= train_cfg['data']['valid_year']]
    X_m4_final['PitProbIn3'] = pd.concat([oof3_s, valid3_s]).reindex(X_m4_final.index)
    m4.train(X_m4_final, y_m4_final, use_log_target=True)

    # Evaluate on test
    metrics_m4 = m4.evaluate(splits_m4['X_test'], splits_m4['y_test'])
    m4.log_to_mlflow(metrics_m4, m4.best_params)
    m4.save(f"{registry_dir}/m4_pipeline.pkl")

    # ═══════════════════════════════════════════════════════════════════════════
    # 7. Train M5 (Short Horizon Regressor)
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("MODEL 5: SHORT HORIZON REGRESSOR")
    print(f"{'='*80}")

    m5_cfg = load_model_config("m5")
    df_m5 = df_m4[df_m4['LapsUntilNextPit'] <= 10].copy()

    X_5 = df_m5.drop(columns=['LapsUntilNextPit'])
    y_5 = df_m5['LapsUntilNextPit']
    groups_m5 = create_groups(df_m5)
    splits_m5 = time_based_split(df_m5, X_5, y_5, groups_m5,
                                  train_cfg['data']['train_end_year'],
                                  train_cfg['data']['valid_year'],
                                  train_cfg['data']['test_year'])

    # Attach PitProbIn3 meta-feature to M5 splits
    splits_m5['X_train']['PitProbIn3'] = oof3_s.reindex(splits_m5['X_train'].index)
    splits_m5['X_valid']['PitProbIn3'] = valid3_s.reindex(splits_m5['X_valid'].index)
    splits_m5['X_test']['PitProbIn3'] = test3_s.reindex(splits_m5['X_test'].index)
    print(f"✓ Short horizon dataset: {len(df_m5)} samples")
    print(f"✓ PitProbIn3 attached to M5")

    m5 = M5Trainer(m5_cfg, train_cfg['mlflow']['tracking_uri'])
    m5.setup_mlflow(train_cfg['mlflow']['experiment_name'])

    m5.optimize_hyperparameters(
        splits_m5['X_train'], splits_m5['y_train'],
        splits_m5['X_valid'], splits_m5['y_valid'],
        n_trials=m5_cfg.get('optuna_trials', 50)
    )

    # Train with 3× sample weights
    X_m5_final = X_5[df_m5["Year"] <= train_cfg['data']['valid_year']]
    y_m5_final = y_5[df_m5["Year"] <= train_cfg['data']['valid_year']]
    m5.train(X_m5_final, y_m5_final, apply_sample_weights=True)

    # Evaluate on test
    metrics_m5 = m5.evaluate(splits_m5['X_test'], splits_m5['y_test'])
    m5.log_to_mlflow(metrics_m5, m5.best_params)
    m5.save(f"{registry_dir}/m5_pipeline.pkl")

    # ═══════════════════════════════════════════════════════════════════════════
    # 8. Summary
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE!")
    print(f"{'='*80}")
    print("\n✅ All models trained and saved:")
    print(f"   • M1: {registry_dir}/m1_pipeline.pkl")
    print(f"   • M2: {registry_dir}/m2_pipeline.pkl")
    print(f"   • M3: {registry_dir}/m3_pipeline.pkl")
    print(f"   • M4: {registry_dir}/m4_pipeline.pkl")
    print(f"   • M5: {registry_dir}/m5_pipeline.pkl")
    print(f"\n✅ MLflow experiments logged: {train_cfg['mlflow']['experiment_name']}")
    print(f"   Run: mlflow ui --port 5000")
    print(f"   Open: http://localhost:5000")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
