from __future__ import annotations

import logging
import argparse
from pathlib import Path

import pandas as pd


from data_loader import DataLoadError, load_and_merge_data
from evaluate import evaluate_predictions, format_metrics
from feature_engineering import add_features, apply_decision_engine
from model import ModelArtifactError, save_model_artifacts, train_and_predict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Green FinOps cost leak detection and sustainability optimization pipeline."
    )
    parser.add_argument("--data-dir", default="data", help="Relative path to the input data directory.")
    parser.add_argument(
        "--output-file",
        default="outputs/final_output.csv",
        help="Relative path to the output CSV file.",
    )
    parser.add_argument(
        "--nrows",
        type=int,
        default=None,
        help="Optional row limit for quicker local testing on very large files.",
    )
    parser.add_argument(
        "--merge-tolerance",
        type=int,
        default=5,
        help="Maximum timestamp gap in seconds for fallback merge_asof matching.",
    )
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--model-file", default="model.pkl", help="Relative path to the saved model artifact.")
    parser.add_argument("--scaler-file", default="scaler.pkl", help="Relative path to the saved scaler artifact.")
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.1,
        help="Expected anomaly ratio for Isolation Forest.",
    )
    parser.add_argument("--test-size", type=float, default=0.3, help="Holdout ratio for evaluation.")
    return parser.parse_args()


def save_results(frame: pd.DataFrame, output_file: str | Path) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return output_path


def setup_logging() -> None:
    """Configure root logger for the pipeline.

    Logs are written to ``pipeline.log`` in the current working directory.
    The format includes timestamp, level and message for easy debugging.
    """
    logging.basicConfig(
        filename='pipeline.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    # Also output to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(console)



def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    args = parse_args()
    logger.info('Starting pipeline with args: %s', args)
    try:
        merged = load_and_merge_data(
            data_dir=args.data_dir,
            nrows=args.nrows,
            tolerance_seconds=args.merge_tolerance,
        )
        featured = add_features(merged, random_state=args.random_state)
        artifacts = train_and_predict(
            featured,
            test_size=args.test_size,
            random_state=args.random_state,
            contamination=args.contamination,
        )
        final_frame = apply_decision_engine(artifacts.test_frame)
        metrics = evaluate_predictions(final_frame)
        output_path = save_results(final_frame, args.output_file)
        save_model_artifacts(
            artifacts.pipeline,
            model_path=args.model_file,
            scaler_path=args.scaler_file,
        )
        logger.info('Pipeline succeeded')
    except (DataLoadError, ValueError, FileNotFoundError, ModelArtifactError) as exc:
        logger.error('Pipeline failed: %s', exc)
        print(f"Pipeline failed: {exc}")
        raise SystemExit(1) from exc

    sample_columns = [
        "server_id",
        "timestamp",
        "vcpu_usage",
        "ram_usage",
        "cost",
        "region",
        "target_region",
        "carbon_intensity",
        "carbon_saving",
        "rule_anomaly",
        "ml_anomaly",
        "vm_status",
        "final_action",
        "reason",
    ]
    logger.info('Sample predictions')
    print("\nSample predictions:")
    print(final_frame[sample_columns].head(10).to_string(index=False))

    logger.info('Metrics: %s', format_metrics(metrics))
    print("\nMetrics:")
    print(format_metrics(metrics))

    print("\nSplit summary:")
    print(f"Train size: {artifacts.train_size}")
    print(f"Test size: {artifacts.test_size}")

    print("\nTrain anomaly distribution:")
    print(artifacts.train_frame["rule_anomaly"].value_counts().to_string())
    print(f"Number of train anomalies: {int(artifacts.train_frame['rule_anomaly'].sum())}")

    print("\nTest anomaly distribution:")
    print(final_frame["rule_anomaly"].value_counts().to_string())
    print(f"Number of test anomalies: {int(final_frame['rule_anomaly'].sum())}")

    print("\nPredicted anomaly distribution:")
    print(final_frame["ml_anomaly"].value_counts().to_string())
    print(f"Number of ML anomalies: {int(final_frame['ml_anomaly'].sum())}")

    print("\nAction distribution:")
    print(final_frame["final_action"].value_counts().to_string())

    print(f"\nSaved output to: {output_path}")
    print(f"Saved model to: {args.model_file}")
    print(f"Saved scaler to: {args.scaler_file}")


if __name__ == "__main__":
    main()
