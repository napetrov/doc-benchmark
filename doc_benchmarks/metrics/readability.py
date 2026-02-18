from __future__ import annotations

import re


SENTENCE_RE = re.compile(r"[.!?]+")
WORD_RE = re.compile(r"[A-Za-zА-Яа-я0-9'-]+")
VOWELS = set("aeiouyаеёиоуыэюяAEIOUYАЕЁИОУЫЭЮЯ")


def _syllables(word: str) -> int:
    count = sum(1 for ch in word if ch in VOWELS)
    return max(1, count)


def score(text: str, grade_max: float = 12.0) -> float:
    words = WORD_RE.findall(text)
    n_words = len(words)
    if n_words == 0:
        return 0.0
    n_sentences = max(1, len(SENTENCE_RE.findall(text)))
    n_syllables = sum(_syllables(w) for w in words)

    # Approx Flesch-Kincaid Grade Level
    grade = 0.39 * (n_words / n_sentences) + 11.8 * (n_syllables / n_words) - 15.59

    # Lower grade is better up to grade_max
    if grade <= 0:
        return 1.0
    if grade >= grade_max:
        return 0.0
    return round(1.0 - (grade / grade_max), 4)
