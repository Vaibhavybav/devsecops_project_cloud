import pandas as pd
import pytest

from evaluate import evaluate_predictions, format_metrics

@pytest.fixture
def sample_frame():
    data = {
        "rule_anomaly": [0, 1, 0, 1, 1, 0],
        "ml_anomaly":   [0, 1, 0, 0, 1, 1],
    }
    return pd.DataFrame(data)

def test_evaluate_predictions(sample_frame):
    metrics = evaluate_predictions(sample_frame)
    # Expected: accuracy = 4/6, precision = 2/3, recall = 2/3, f1 = 2/3
    assert pytest.approx(metrics["accuracy"], 0.001) == 4 / 6
    assert pytest.approx(metrics["precision"], 0.001) == 2 / 3
    assert pytest.approx(metrics["recall"], 0.001) == 2 / 3
    assert pytest.approx(metrics["f1_score"], 0.001) == 2 / 3
    # Confusion matrix should be a list of lists
    assert isinstance(metrics["confusion_matrix"], list)
    assert all(isinstance(row, list) for row in metrics["confusion_matrix"])

def test_format_metrics(sample_frame):
    metrics = evaluate_predictions(sample_frame)
    formatted = format_metrics(metrics)
    for key in ["Accuracy", "Precision", "Recall", "F1 Score", "Confusion Matrix"]:
        assert key in formatted
    assert "\n" in formatted
