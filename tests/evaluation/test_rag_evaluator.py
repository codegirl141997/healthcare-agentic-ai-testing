
import pytest

from src.evaluation.rag_evaluator import RAGEvaluator


@pytest.fixture
def evaluator():
    return RAGEvaluator()


def test_grounded_answer_passes(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="Appointment confirmed after booking service confirmation.",
        context=(
            "An appointment is confirmed only after the booking "
            "service returns successful confirmation."
        ),
    )

    assert result["passed"] is True
    assert result["coverage"] >= 0.5


def test_unsupported_answer_fails_groundedness(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="Volcanoes contain molten lava and erupt frequently.",
        context="An appointment must use an available slot.",
    )

    assert result["passed"] is False


def test_relevant_answer_passes(evaluator):
    result = evaluator.evaluate_relevance(
        question="When is an appointment confirmed?",
        answer="An appointment is confirmed after booking service confirmation.",
    )

    assert result["passed"] is True


def test_unrelated_answer_fails_relevance(evaluator):
    result = evaluator.evaluate_relevance(
        question="How is an appointment confirmed?",
        answer="Volcanoes contain molten lava.",
    )

    assert result["passed"] is False


def test_missing_context_requires_abstention(evaluator):
    result = evaluator.evaluate_abstention(
        answer="I cannot answer from the available information.",
        context_found=False,
    )

    assert result["passed"] is True
    assert result["abstained"] is True


def test_unconfirmed_booking_claim_is_flagged(evaluator):
    result = evaluator.evaluate_unsupported_claims(
        answer="Your appointment is confirmed.",
        booking_confirmed=False,
    )

    assert result["passed"] is False
    assert result["violations"]


def test_confirmed_booking_claim_is_allowed(evaluator):
    result = evaluator.evaluate_unsupported_claims(
        answer="Your appointment is confirmed.",
        booking_confirmed=True,
    )

    assert result["passed"] is True


def test_retrieved_source_is_valid(evaluator):
    result = evaluator.evaluate_sources(
        reported_sources=["appointment_rules.txt"],
        retrieved_sources=["appointment_rules.txt", "cancellation_rules.txt"],
    )

    assert result["passed"] is True


def test_fabricated_source_is_rejected(evaluator):
    result = evaluator.evaluate_sources(
        reported_sources=["invented_policy.txt"],
        retrieved_sources=["appointment_rules.txt"],
    )

    assert result["passed"] is False


def test_groundedness_rejects_empty_context(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="An appointment is confirmed.",
        context="",
    )

    assert result["passed"] is False


def test_evaluator_rejects_empty_answer(evaluator):
    with pytest.raises(ValueError, match="non-empty string"):
        evaluator.evaluate_groundedness("", "appointment confirmation")


def test_abstention_requires_boolean_context_flag(evaluator):
    with pytest.raises(ValueError, match="boolean"):
        evaluator.evaluate_abstention(
            "I cannot answer.",
            context_found="false",
        )


def test_groundedness_rejects_invalid_answer_type(evaluator):
    with pytest.raises(ValueError):
        evaluator.evaluate_groundedness(None, "Appointment rules")


def test_groundedness_accepts_explicit_unavailability(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="This information is unavailable.",
        context="",
    )

    assert result["passed"] is False


def test_groundedness_rejects_answer_without_meaningful_overlap(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="the is and or",
        context="the is and or",
    )

    assert result["passed"] is False


def test_relevance_rejects_empty_question(evaluator):
    with pytest.raises(ValueError):
        evaluator.evaluate_relevance(
            question="",
            answer="An appointment is confirmed.",
        )


def test_relevance_rejects_question_without_meaningful_terms(evaluator):
    result = evaluator.evaluate_relevance(
        question="the is and or",
        answer="An appointment is confirmed.",
    )

    assert result["passed"] is False


def test_abstention_fails_when_context_is_missing_but_answer_guesses(evaluator):
    result = evaluator.evaluate_abstention(
        answer="Your appointment is confirmed.",
        context_found=False,
    )

    assert result["passed"] is False
    assert result["abstained"] is False


def test_abstention_fails_when_context_exists_but_answer_abstains(evaluator):
    result = evaluator.evaluate_abstention(
        answer="I cannot answer from the available information.",
        context_found=True,
    )

    assert result["passed"] is False


def test_sources_reject_empty_reported_sources(evaluator):
    result = evaluator.evaluate_sources(
        reported_sources=[],
        retrieved_sources=["appointment_rules.txt"],
    )

    assert result["passed"] is False


def test_sources_reject_non_list_input(evaluator):
    with pytest.raises(ValueError):
        evaluator.evaluate_sources(
            reported_sources="appointment_rules.txt",
            retrieved_sources=["appointment_rules.txt"],
        )


def test_sources_reject_blank_source_names(evaluator):
    result = evaluator.evaluate_sources(
        reported_sources=[""],
        retrieved_sources=["appointment_rules.txt"],
    )

    assert result["passed"] is False


def test_unconfirmed_cancellation_claim_is_flagged(evaluator):
    result = evaluator.evaluate_unsupported_claims(
        answer="Your appointment was cancelled.",
        cancellation_confirmed=False,
    )

    assert result["passed"] is False
    assert result["violations"]


def test_confirmed_cancellation_claim_is_allowed(evaluator):
    result = evaluator.evaluate_unsupported_claims(
        answer="Your appointment was cancelled.",
        cancellation_confirmed=True,
    )

    assert result["passed"] is True


def test_negated_booking_claim_is_not_flagged(evaluator):
    result = evaluator.evaluate_unsupported_claims(
        answer="I should not claim that the appointment is confirmed.",
        booking_confirmed=False,
    )

    assert result["passed"] is True
def test_groundedness_accepts_specific_unavailability(evaluator):
    result = evaluator.evaluate_groundedness(
        answer="This information is unavailable.",
        context="The hospital provides routine medical care.",
    )

    assert result["passed"] is True
    assert result["coverage"] == 1.0


def test_relevance_rejects_empty_answer(evaluator):
    with pytest.raises(ValueError, match="non-empty string"):
        evaluator.evaluate_relevance(
            question="When is the appointment confirmed?",
            answer="",
        )


def test_abstention_rejects_empty_answer(evaluator):
    with pytest.raises(ValueError, match="non-empty string"):
        evaluator.evaluate_abstention(
            answer="",
            context_found=False,
        )


def test_sources_reject_non_list_retrieved_sources(evaluator):
    with pytest.raises(
        ValueError,
        match="retrieved_sources must be a list",
    ):
        evaluator.evaluate_sources(
            reported_sources=["appointment_rules.txt"],
            retrieved_sources="appointment_rules.txt",
        )


def test_unsupported_claims_reject_empty_answer(evaluator):
    with pytest.raises(ValueError, match="non-empty string"):
        evaluator.evaluate_unsupported_claims("")


def test_unsupported_claims_reject_non_boolean_booking_confirmation(
    evaluator,
):
    with pytest.raises(
        ValueError,
        match="booking_confirmed must be a boolean",
    ):
        evaluator.evaluate_unsupported_claims(
            "Booking is complete.",
            booking_confirmed="yes",
        )


def test_unsupported_claims_reject_non_boolean_cancellation_confirmation(
    evaluator,
):
    with pytest.raises(
        ValueError,
        match="cancellation_confirmed must be a boolean",
    ):
        evaluator.evaluate_unsupported_claims(
            "Cancellation requested.",
            cancellation_confirmed="yes",
        )
        
        
def test_abstention_accepts_specific_unavailability(evaluator):
    result = evaluator.evaluate_abstention(
        answer="This information is unavailable.",
        context_found=True,
    )

    assert result["passed"] is True
    assert result["abstained"] is True
