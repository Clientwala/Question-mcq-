"""
Question Parser Service.

Parses questions from extracted PDF text using regex patterns.
This is the most critical and complex component.
"""
import re
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuestion:
    """Structured question data."""
    number: int
    question_text: List[str]
    options: List[str]
    correct_option_idx: int
    solution_text: List[str]
    has_diagram: bool
    confidence: float  # 0.0-1.0


class QuestionParser:
    """
    Parse questions from extracted PDF text.

    Uses multi-stage regex-based parsing with confidence scoring.
    """

    # Regex patterns (configurable for different PDF formats)
    PATTERNS = {
        # Question number: "Q1.", "1.", "Q.1", "101)", "Q 101."
        'question_number': r'(?:Q\.?\s*)?(\d+)[\.\)]\s*',

        # Options: "(a)", "a)", "A.", "(A)", "a.", etc.
        'option_marker': r'\(?\s*([a-dA-D])\s*[\)\.]?\s*',

        # Answer patterns: "Ans: (c)", "Answer: c", "Ans. (C)", "Correct: B"
        'answer': r'(?:Ans(?:wer)?|Correct)\s*[:\.]\s*\(?\s*([a-dA-D])\s*\)?',

        # Solution markers: "Solution:", "Explanation:", "Sol:", "Sol."
        'solution': r'(?:Solution|Explanation|Sol)\s*[:\.]\s*',

        # Diagram indicators
        'diagram': r'(?:diagram|figure|image|graph|chart|table|see\s+(?:above|below|figure)|shown\s+in|refer\s+to)',
    }

    def __init__(self):
        """Initialize parser with compiled regex patterns."""
        self.compiled_patterns = {
            key: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for key, pattern in self.PATTERNS.items()
        }

    async def parse_questions(
        self,
        text: str,
        start_q: int,
        end_q: int
    ) -> List[ParsedQuestion]:
        """
        Parse multiple questions from text.

        Strategy:
        1. Split text into question blocks by number markers
        2. Parse each block independently
        3. Validate and score confidence
        4. Return structured data

        Args:
            text: Extracted PDF text
            start_q: First question number to extract
            end_q: Last question number to extract

        Returns:
            List of ParsedQuestion objects

        Raises:
            ValueError: If no questions found or parsing fails
        """
        logger.info(f"Parsing questions {start_q} to {end_q}")

        # Stage 1: Split into question blocks
        question_blocks = self._split_into_blocks(text, start_q, end_q)
        logger.info(f"Found {len(question_blocks)} question blocks")

        if not question_blocks:
            raise ValueError(f"No questions found in range {start_q}-{end_q}")

        # Stage 2: Parse each block
        questions = []
        for block in question_blocks:
            try:
                parsed = self._parse_single_question(block)
                if parsed:
                    questions.append(parsed)
                    logger.debug(f"Parsed Q{parsed.number} (confidence: {parsed.confidence:.2f})")
                else:
                    logger.warning(f"Failed to parse question {block['number']}")
            except Exception as e:
                logger.error(f"Error parsing question {block.get('number', '?')}: {e}")
                continue

        # Stage 3: Validate sequence
        self._validate_question_sequence(questions, start_q, end_q)

        logger.info(f"Successfully parsed {len(questions)} questions")
        return questions

    def _split_into_blocks(
        self,
        text: str,
        start_q: int,
        end_q: int
    ) -> List[Dict]:
        """
        Split text into individual question blocks.

        Approach:
        - Find all question number markers
        - Split text between consecutive markers
        - Filter by question range

        Returns:
            List of dictionaries: [{'number': int, 'text': str}, ...]
        """
        blocks = []
        pattern = self.compiled_patterns['question_number']

        # Find all matches with positions
        matches = list(pattern.finditer(text))
        logger.debug(f"Found {len(matches)} question number markers")

        for i, match in enumerate(matches):
            q_num = int(match.group(1))

            # Filter by range
            if q_num < start_q or q_num > end_q:
                continue

            # Extract text from this question to next
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block_text = text[start:end].strip()

            blocks.append({
                'number': q_num,
                'text': block_text
            })

        return blocks

    def _parse_single_question(self, block: Dict) -> Optional[ParsedQuestion]:
        """
        Parse a single question block into structured data.

        Steps:
        1. Extract question text (before first option)
        2. Extract options (a, b, c, d)
        3. Find correct answer
        4. Extract solution text
        5. Detect diagrams

        Returns:
            ParsedQuestion or None if parsing fails
        """
        text = block['text']
        q_num = block['number']

        try:
            # Extract question text
            question_lines = self._extract_question_text(text)
            if not question_lines:
                logger.warning(f"Q{q_num}: No question text found")
                return None

            # Extract options
            options = self._extract_options(text)
            if len(options) != 4:
                logger.warning(f"Q{q_num}: Found {len(options)} options (expected 4)")
                # Try alternative parsing
                options = self._extract_options_alternative(text)
                if len(options) != 4:
                    logger.error(f"Q{q_num}: Could not extract 4 options")
                    return None

            # Find correct answer
            correct_idx = self._find_correct_answer(text)
            if correct_idx is None:
                logger.warning(f"Q{q_num}: Could not find correct answer, defaulting to 0")
                correct_idx = 0  # Default to first option

            # Extract solution
            solution_lines = self._extract_solution(text)
            if not solution_lines:
                logger.warning(f"Q{q_num}: No solution text found")
                solution_lines = ["Solution not available"]

            # Detect diagrams
            has_diagram = self._detect_diagram(text)
            if has_diagram:
                logger.info(f"Q{q_num}: Diagram detected")

            # Calculate confidence score
            confidence = self._calculate_confidence(
                question_lines, options, correct_idx, solution_lines
            )

            return ParsedQuestion(
                number=q_num,
                question_text=question_lines,
                options=options,
                correct_option_idx=correct_idx,
                solution_text=solution_lines,
                has_diagram=has_diagram,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Q{q_num}: Parsing error: {e}", exc_info=True)
            return None

    def _extract_question_text(self, text: str) -> List[str]:
        """
        Extract question text (before first option).

        Strategy: Text from question number to first option marker.
        """
        # Find first option marker
        option_pattern = self.compiled_patterns['option_marker']
        option_match = option_pattern.search(text)

        if option_match:
            # Question text is from start to first option
            question_text = text[:option_match.start()].strip()
        else:
            # No options found, take first reasonable chunk
            question_text = text[:500].strip()

        # Remove question number prefix
        q_num_pattern = self.compiled_patterns['question_number']
        question_text = q_num_pattern.sub('', question_text, count=1).strip()

        # Split into lines and clean
        lines = [line.strip() for line in question_text.split('\n') if line.strip()]
        return lines if lines else []

    def _extract_options(self, text: str) -> List[str]:
        """
        Extract option texts.

        Pattern: (a) Option text (b) Option text (c) Option text (d) Option text
        """
        options = []
        pattern = self.compiled_patterns['option_marker']

        # Find all option markers
        matches = list(pattern.finditer(text))

        # Take first 4 matches (a, b, c, d)
        for i in range(min(4, len(matches))):
            match = matches[i]

            # Extract text from this option to next (or to answer/solution marker)
            start = match.end()
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                # Last option: find answer/solution marker
                answer_match = self.compiled_patterns['answer'].search(text, start)
                sol_match = self.compiled_patterns['solution'].search(text, start)

                end = min(
                    answer_match.start() if answer_match else len(text),
                    sol_match.start() if sol_match else len(text)
                )

            option_text = text[start:end].strip()

            # Clean up option text
            option_text = self._clean_option_text(option_text)

            options.append(option_text)

        return options

    def _extract_options_alternative(self, text: str) -> List[str]:
        """
        Alternative option extraction method (fallback).

        Uses line-by-line approach for differently formatted options.
        """
        options = []
        lines = text.split('\n')

        for line in lines:
            # Check if line starts with option marker
            if re.match(r'^\s*\(?\s*[a-dA-D]\s*[\)\.]', line):
                # Remove marker and clean
                option_text = re.sub(r'^\s*\(?\s*[a-dA-D]\s*[\)\.]?\s*', '', line).strip()
                if option_text:
                    options.append(option_text)

                if len(options) == 4:
                    break

        return options

    def _clean_option_text(self, text: str) -> str:
        """Clean and normalize option text."""
        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove trailing answer markers
        text = re.sub(r'\s*(?:Ans|Answer|Correct).*$', '', text, flags=re.IGNORECASE)

        return text.strip()

    def _find_correct_answer(self, text: str) -> Optional[int]:
        """
        Find correct answer from answer markers.

        Patterns: "Ans: (c)", "Answer: B", "Ans. (d)", "Correct: C"

        Returns:
            Index 0-3 for options a-d, or None if not found
        """
        pattern = self.compiled_patterns['answer']
        match = pattern.search(text)

        if match:
            answer_letter = match.group(1).lower()
            # Convert 'a' -> 0, 'b' -> 1, 'c' -> 2, 'd' -> 3
            return ord(answer_letter) - ord('a')

        return None

    def _extract_solution(self, text: str) -> List[str]:
        """
        Extract solution text.

        Strategy: Text after "Solution:" / "Explanation:" marker
        """
        pattern = self.compiled_patterns['solution']
        match = pattern.search(text)

        if match:
            solution_text = text[match.end():].strip()

            # Split into lines
            lines = [line.strip() for line in solution_text.split('\n') if line.strip()]
            return lines if lines else []

        # Fallback: text after answer marker
        answer_pattern = self.compiled_patterns['answer']
        answer_match = answer_pattern.search(text)

        if answer_match:
            solution_text = text[answer_match.end():].strip()
            lines = [line.strip() for line in solution_text.split('\n') if line.strip()]
            return lines if lines else []

        return []

    def _detect_diagram(self, text: str) -> bool:
        """
        Detect if question contains diagram.

        Indicators:
        1. Text mentions: "diagram", "figure", "image", "graph"
        2. Placeholder text: "see figure above", "refer to diagram"
        """
        pattern = self.compiled_patterns['diagram']
        return bool(pattern.search(text))

    def _calculate_confidence(
        self,
        question: List[str],
        options: List[str],
        correct_idx: Optional[int],
        solution: List[str]
    ) -> float:
        """
        Calculate parsing confidence score (0.0-1.0).

        Scoring:
        - Has question text: +0.3
        - Has 4 options: +0.3
        - Has correct answer: +0.2
        - Has solution: +0.2
        """
        score = 0.0

        if question and len(question) > 0:
            score += 0.3

        if len(options) == 4:
            score += 0.3

        if correct_idx is not None and 0 <= correct_idx < 4:
            score += 0.2

        if solution and len(solution) > 0:
            score += 0.2

        return round(score, 2)

    def _validate_question_sequence(
        self,
        questions: List[ParsedQuestion],
        start_q: int,
        end_q: int
    ):
        """
        Validate that question sequence is complete.

        Logs warnings for missing questions.
        """
        expected = set(range(start_q, end_q + 1))
        actual = {q.number for q in questions}
        missing = expected - actual

        if missing:
            logger.warning(f"Missing questions: {sorted(missing)}")

        # Check for duplicates
        numbers = [q.number for q in questions]
        duplicates = {n for n in numbers if numbers.count(n) > 1}

        if duplicates:
            logger.warning(f"Duplicate questions found: {sorted(duplicates)}")

    def to_dict_list(self, questions: List[ParsedQuestion]) -> List[Dict]:
        """Convert list of ParsedQuestion to list of dictionaries."""
        return [asdict(q) for q in questions]
