"""
Test script for PDF parsing and document generation.

Tests the complete pipeline:
1. PDF text extraction
2. Question parsing
3. Word document generation
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_parser import PDFParser
from app.services.question_parser import QuestionParser
from app.services.document_generator import DocumentGenerator


async def test_pdf_parsing():
    """Test PDF parsing with actual PDF file."""

    # Configuration
    PDF_PATH = "../chapter -2 168-221 (1).pdf"
    PAGE_START = 1  # Adjust based on actual PDF
    PAGE_END = 5    # Start with just a few pages for testing
    QUESTION_START = 2  # Adjust based on PDF content (actual questions start at 2)
    QUESTION_END = 9    # Test with ~8 questions first
    OUTPUT_PATH = "../test_output.docx"

    print("=" * 60)
    print("PDF Question Parser - Test Script")
    print("=" * 60)
    print()

    # Step 1: Extract PDF text
    print(f"Step 1: Extracting text from PDF...")
    print(f"  PDF: {PDF_PATH}")
    print(f"  Pages: {PAGE_START} to {PAGE_END}")
    print()

    try:
        parser = PDFParser()

        # Validate PDF first
        await parser.validate_pdf(PDF_PATH)
        print("  [OK] PDF validated")

        # Get PDF info
        pdf_info = await parser.get_pdf_info(PDF_PATH)
        print(f"  [OK] Total pages: {pdf_info['total_pages']}")

        # Extract text
        pdf_text = await parser.extract_text(PDF_PATH, PAGE_START, PAGE_END)
        print(f"  [OK] Extracted {len(pdf_text)} characters")
        print()

        # Show sample text
        print("Sample text (first 500 chars):")
        print("-" * 60)
        print(pdf_text[:500])
        print("-" * 60)
        print()

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return False

    # Step 2: Parse questions
    print(f"Step 2: Parsing questions {QUESTION_START} to {QUESTION_END}...")
    print()

    try:
        question_parser = QuestionParser()
        questions = await question_parser.parse_questions(
            pdf_text,
            QUESTION_START,
            QUESTION_END
        )

        print(f"  [OK] Parsed {len(questions)} questions")
        print()

        # Show parsed questions
        for q in questions:
            print(f"Question {q.number}:")
            print(f"  Question text: {q.question_text[0][:80]}...")
            print(f"  Options: {len(q.options)}")
            print(f"  Correct: {chr(97 + q.correct_option_idx)} ({q.options[q.correct_option_idx][:50]}...)")
            print(f"  Solution: {len(q.solution_text)} lines")
            print(f"  Diagram: {q.has_diagram}")
            print(f"  Confidence: {q.confidence}")
            print()

        # Statistics
        avg_confidence = sum(q.confidence for q in questions) / len(questions) if questions else 0
        low_confidence = sum(1 for q in questions if q.confidence < 0.7)

        print(f"Statistics:")
        print(f"  Average confidence: {avg_confidence:.2f}")
        print(f"  Low confidence (<0.7): {low_confidence}")
        print(f"  Diagrams detected: {sum(1 for q in questions if q.has_diagram)}")
        print()

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Generate Word document
    print(f"Step 3: Generating Word document...")
    print(f"  Output: {OUTPUT_PATH}")
    print()

    try:
        doc_gen = DocumentGenerator()

        # Validate questions first
        await doc_gen.validate_questions(questions)
        print("  [OK] Questions validated")

        # Generate document
        config = {
            'question_start': QUESTION_START,
            'question_end': QUESTION_END,
            'chapter_name': 'Test Chapter'
        }

        def progress_callback(progress):
            percent = int(progress * 100)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '#' * filled + '-' * (bar_length - filled)
            print(f"\r  Progress: [{bar}] {percent}%", end='', flush=True)

        output_path = await doc_gen.create_document(
            questions,
            config,
            OUTPUT_PATH,
            progress_callback=progress_callback
        )

        print()
        print(f"  [OK] Document created: {output_path}")
        print()

        # Get document stats
        stats = await doc_gen.get_document_stats(questions)
        print(f"Document statistics:")
        for key, value in stats.items():
            if key != 'question_numbers':
                print(f"  {key}: {value}")
        print()

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Open the generated Word document to verify formatting")
    print("2. Check if questions, options, and solutions are correct")
    print("3. Adjust regex patterns if needed")
    print("4. Test with full page range")
    print()

    return True


async def main():
    """Main test function."""
    success = await test_pdf_parsing()

    if not success:
        print("\n[WARNING] Tests failed! Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
