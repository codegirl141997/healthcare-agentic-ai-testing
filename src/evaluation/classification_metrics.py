
def calculate_metrics(y_true, y_pred):
    """
    Calculate binary classification metrics.

    Label 1 = positive class
    Label 0 = negative class
    """

    if len(y_true) != len(y_pred):
        raise ValueError(
            "Actual and predicted labels must have equal length"
        )

    if len(y_true) == 0:
        raise ValueError("At least one prediction is required")

    if any(label not in (0, 1) for label in y_true + y_pred):
        raise ValueError("Labels must be 0 or 1")

    tp = sum(
        actual == 1 and predicted == 1
        for actual, predicted in zip(y_true, y_pred)
    )
    tn = sum(
        actual == 0 and predicted == 0
        for actual, predicted in zip(y_true, y_pred)
    )
    fp = sum(
        actual == 0 and predicted == 1
        for actual, predicted in zip(y_true, y_pred)
    )
    fn = sum(
        actual == 1 and predicted == 0
        for actual, predicted in zip(y_true, y_pred)
    )

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / len(y_true)

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "confusion_matrix": {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
        },
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "accuracy": accuracy,
    }
