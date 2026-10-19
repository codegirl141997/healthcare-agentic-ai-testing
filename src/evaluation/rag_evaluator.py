import re


class RAGEvaluator:
    """Deterministic, heuristic quality checks for RAG answers."""

    ABSTENTION_PHRASES = (
        "cannot answer",
        "cannot be answered",
        "information is unavailable",
        "information is not available",
        "not available in the provided context",
        "does not contain information about",
        "policy is unavailable",
        "policy is not available",
        "don't have enough information",
        "do not have enough information",
    )

    NEGATION_PHRASES = (
        "must not claim",
        "should not claim",
        "cannot claim",
        "can not claim",
        "do not claim",
        "don't claim",
        "never claim",
        "must not state",
        "should not state",
    )

    def _normalize(self, text: str) -> str:
        """Normalize punctuation and whitespace for heuristic matching."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s']", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _is_explicit_abstention(self, answer: str) -> bool:
        normalized = self._normalize(answer)
        return any(
            phrase in normalized
            for phrase in self.ABSTENTION_PHRASES
        )

    def evaluate_groundedness(self, answer: str, context: str) -> dict:
        """Check answer/context overlap, recognizing explicit abstentions."""
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer must be a non-empty string.")

        if not isinstance(context, str) or not context.strip():
            return {
                "passed": False,
                "reason": "No context was provided.",
            }

        normalized_answer = self._normalize(answer)

        specific_unavailability = (
            "information is unavailable" in normalized_answer
            or "information is not available" in normalized_answer
            or "not available in the provided context" in normalized_answer
            or "does not contain information about" in normalized_answer
            or "policy is unavailable" in normalized_answer
            or "policy is not available" in normalized_answer
        )

        if specific_unavailability:
            return {
                "passed": True,
                "coverage": 1.0,
                "reason": (
                    "Explicit abstention recognized; verify that the "
                    "retrieved context truly lacks the requested information."
                ),
            }

        ignored_words = {
            "a", "an", "and", "are", "as", "at", "be", "been",
            "by", "for", "from", "has", "have", "i", "in", "is",
            "it", "of", "on", "or", "that", "the", "this", "to",
            "was", "were", "what", "when", "which", "who", "will",
            "with", "only", "after",
        }

        context_words = set(self._normalize(context).split())
        answer_words = set(normalized_answer.split())
        meaningful_words = answer_words - ignored_words

        if not meaningful_words:
            return {
                "passed": False,
                "reason": "Answer contains no meaningful terms to evaluate.",
            }

        supported_words = meaningful_words & context_words
        coverage = len(supported_words) / len(meaningful_words)

        return {
            "passed": coverage >= 0.5,
            "coverage": round(coverage, 3),
            "reason": (
                "Sufficient word overlap with context."
                if coverage >= 0.5
                else "Answer contains terms not sufficiently supported by context."
            ),
        }

    def evaluate_relevance(self, question: str, answer: str) -> dict:
        """Check whether an answer overlaps meaningfully with a question."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer must be a non-empty string.")

        stop_words = {
            "a", "an", "and", "are", "can", "do", "does", "for",
            "how", "i", "is", "it", "of", "on", "or", "the",
            "to", "was", "what", "when", "where", "which", "who",
            "why", "with",
        }

        question_words = set(self._normalize(question).split()) - stop_words
        answer_words = set(self._normalize(answer).split()) - stop_words

        if not question_words:
            return {
                "passed": False,
                "reason": "Question contains no meaningful terms.",
            }

        overlap = question_words & answer_words
        coverage = len(overlap) / len(question_words)

        return {
            "passed": coverage >= 0.3,
            "coverage": round(coverage, 3),
            "reason": (
                "Answer overlaps with question terms."
                if coverage >= 0.3
                else "Answer may not address the question."
            ),
        }

    def evaluate_abstention(self, answer: str, context_found: bool) -> dict:
        """Check whether the answer appropriately abstains."""
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer must be a non-empty string.")

        if not isinstance(context_found, bool):
            raise ValueError("context_found must be a boolean.")

        abstained = self._is_explicit_abstention(answer)
        normalized_answer = self._normalize(answer)

        specific_unavailability = (
            "information is unavailable" in normalized_answer
            or "information is not available" in normalized_answer
            or "not available in the provided context" in normalized_answer
            or "does not contain information about" in normalized_answer
            or "policy is unavailable" in normalized_answer
            or "policy is not available" in normalized_answer
        )

        if specific_unavailability:
            passed = True
        else:
            passed = abstained if not context_found else not abstained

        return {
            "passed": passed,
            "abstained": abstained,
            "reason": (
                "Appropriate abstention recognized."
                if passed and abstained
                else (
                    "Abstention behavior matches context availability."
                    if passed
                    else "Abstention behavior does not match context availability."
                )
            ),
        }

    def evaluate_sources(
        self,
        reported_sources: list[str],
        retrieved_sources: list[str],
    ) -> dict:
        """Check that reported source names came from retrieved documents."""
        if not isinstance(reported_sources, list):
            raise ValueError("reported_sources must be a list.")

        if not isinstance(retrieved_sources, list):
            raise ValueError("retrieved_sources must be a list.")

        valid = bool(reported_sources) and all(
            isinstance(source, str)
            and source.strip()
            and source in retrieved_sources
            for source in reported_sources
        )

        return {
            "passed": valid,
            "reason": (
                "Reported sources match retrieved documents."
                if valid
                else "Reported sources are missing or were not retrieved."
            ),
        }

    def evaluate_unsupported_claims(
        self,
        answer: str,
        booking_confirmed: bool = False,
        cancellation_confirmed: bool = False,
    ) -> dict:
        """Flag positive success claims lacking service confirmation."""
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer must be a non-empty string.")

        if not isinstance(booking_confirmed, bool):
            raise ValueError("booking_confirmed must be a boolean.")

        if not isinstance(cancellation_confirmed, bool):
            raise ValueError("cancellation_confirmed must be a boolean.")

        text = self._normalize(answer)
        violations = []

        claim_groups = [
            (
                booking_confirmed,
                (
                    "appointment is confirmed",
                    "appointment has been confirmed",
                    "booking succeeded",
                    "booking was successful",
                ),
            ),
            (
                cancellation_confirmed,
                (
                    "appointment was cancelled",
                    "appointment has been cancelled",
                ),
            ),
        ]

        for confirmed, phrases in claim_groups:
            if confirmed:
                continue

            for phrase in phrases:
                start = 0
                while True:
                    index = text.find(phrase, start)
                    if index == -1:
                        break

                    prefix = text[max(0, index - 65):index]
                    is_negated = any(
                        negation in prefix
                        for negation in self.NEGATION_PHRASES
                    )

                    if not is_negated and phrase not in violations:
                        violations.append(phrase)

                    start = index + len(phrase)

        return {
            "passed": not violations,
            "violations": violations,
            "reason": (
                "No unconfirmed positive booking or cancellation claim detected."
                if not violations
                else "Potential unsupported success claim detected."
            ),
        }
