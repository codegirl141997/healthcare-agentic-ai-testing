
import pytest

from src.evaluation.classification_metrics import calculate_metrics


def test_calculate_metrics_returns_correct_values():
    actual = [1, 1, 0, 0, 1]
    predicted = [1, 0, 0, 1, 1]

    result = calculate_metrics(actual, predicted)

    assert result["confusion_matrix"] == {
        "TP": 2,
        "FP": 1,
        "TN": 1,
        "FN": 1,
    }
    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == pytest.approx(2 / 3)
    assert result["f1_score"] == pytest.approx(2 / 3)
    assert result["accuracy"] == pytest.approx(0.6)


def test_perfect_predictions_return_100_percent_metrics():
    result = calculate_metrics([1, 0, 1, 0], [1, 0, 1, 0])

    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1_score"] == 1.0
    assert result["accuracy"] == 1.0


def test_precision_is_zero_when_no_positive_predictions():
    result = calculate_metrics([1, 0], [0, 0])

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1_score"] == 0.0


def test_recall_is_zero_when_no_actual_positive_cases():
    result = calculate_metrics([0, 0], [1, 0])

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1_score"] == 0.0


def test_empty_input_is_rejected():
    with pytest.raises(ValueError, match="At least one prediction"):
        calculate_metrics([], [])


def test_mismatched_input_lengths_are_rejected():
    with pytest.raises(ValueError, match="equal length"):
        calculate_metrics([1, 0], [1])


def test_invalid_labels_are_rejected():
    with pytest.raises(ValueError, match="Labels must be 0 or 1"):
        calculate_metrics([1, 2], [1, 0])
