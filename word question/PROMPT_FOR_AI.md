# PROMPT FOR CURSOR / CLAUDE CODE

## PROJECT CONTEXT
I am working on a document generation system for a client who has multiple PDF textbooks containing questions. The goal is to extract questions from PDFs and format them into structured Word documents (.docx) with specific formatting requirements.

## CURRENT TASK
Generate formatted Word documents from KVS PGT (Kendriya Vidyalaya Sangathan Post Graduate Teacher) examination question papers.

## INPUT
- **Source:** PDF file containing questions (e.g., `KVS_NVS_PGT_COMPUTER_SCIENCE_SOLVED_PAPERS___PRACTICE_BOOK.pdf`)
- **Format:** Questions numbered sequentially (Q101, Q102, etc.)
- **Content:** Each question has:
  - Question text (may span multiple lines)
  - 4 options (a, b, c, d)
  - Correct answer indicator
  - Solution/explanation text
  - Some questions have diagrams/figures

## OUTPUT REQUIREMENTS

### Document Format
- **File type:** Microsoft Word (.docx)
- **Page margins:**
  - Left: 2.4cm
  - Right: 2.4cm
  - Top: 3.5cm
  - Bottom: 2.4cm

### Table Structure (8 rows × 3 columns per question)
Each question must be in a centered table with the following structure:

| Row | Column 1 (Label) | Column 2 (Content) | Column 3 (Status) |
|-----|------------------|-------------------|-------------------|
| 0 | Question | [Question text merged across cols 2-3] | |
| 1 | Type | Multiple_choice [merged across cols 2-3] | |
| 2 | Option | Option A text | correct/incorrect |
| 3 | Option | Option B text | correct/incorrect |
| 4 | Option | Option C text | correct/incorrect |
| 5 | Option | Option D text | correct/incorrect |
| 6 | Solution | [Solution text merged across cols 2-3] | |
| 7 | Marks | 1 | 0.25 |

### Column Widths
- **Column 1 (Labels):** 1.5cm (narrow - contains "Question", "Type", "Option", "Solution", "Marks")
- **Column 2 (Content):** 8.5cm (wide - main content area)
- **Column 3 (Right):** 3.0cm (for "correct"/"incorrect" indicators)
- **Total:** 13cm table width

### Table Position
- **CRITICAL:** Table must be CENTER ALIGNED on the page
- Equal margins on left and right sides
- NOT left-aligned or right-aligned

### Formatting Details
- **Font:** Times New Roman
- **Size:** 14pt
- **Weight:** Bold
- **Alignment:** Justify (for all text content)
- **Borders:** All cells have single black borders (4pt width)
- **Cell padding:** 120 dxa top/bottom, 100 dxa left/right
- **Type row:** "Multiple_choice" text in column 2, columns 2+3 merged (NO vertical line between them)
- **Page break:** After each question (except the last one)

## DIAGRAM HANDLING
- Some questions contain diagrams (circuit diagrams, graphs, trees, etc.)
- Detection keywords: "diagram", "figure", "following table", "below shows"
- When detected: Add note "[DIAGRAM PRESENT - See PDF]" in question text
- Track and report which questions have diagrams

## PDF PARSING REQUIREMENTS

### Text Extraction
- Use `pdftotext` command-line tool with `-raw` flag
- Extract specific page range from PDF
- Preserve line breaks and structure

### Question Detection
- Questions start with number format: "101.", "102.", etc.
- May have bilingual text (English + Hindi/other language)
- Parse until next question number or "Ans." marker

### Answer Parsing
- Correct answer indicated by "Ans." or "Answer:" marker
- Format: "Ans. (a)", "Ans. (b)", etc.
- Extract the letter (a/b/c/d) and convert to index (0/1/2/3)

### Solution Extraction
- Text after "Ans." line until next question
- May contain multiple paragraphs
- Preserve formatting (bullets, numbered lists, formulas)
- Handle special characters: subscripts, superscripts, mathematical symbols

## TECHNICAL STACK
- **Python 3.x**
- **python-docx:** For Word document generation
- **pdftotext (poppler-utils):** For PDF text extraction
- **subprocess:** To call pdftotext command

## ERROR HANDLING
Common issues to handle:
1. **PDF extraction fails:** Check if poppler-utils installed
2. **Parsing errors:** Questions with unusual format
3. **Unicode issues:** Special mathematical symbols
4. **Diagram detection:** May miss some diagrams
5. **Answer format variations:** "Ans (a)" vs "Ans. (a):" vs "Answer: a"

## CONFIGURATION
All settings are in CONFIG dictionary:
- PDF path and page range
- Question number range
- Output file path
- Margins, widths, fonts
- Easy to modify for different PDFs

## SAMPLE USAGE
```python
CONFIG = {
    'pdf_path': 'questions.pdf',
    'year': 2013,
    'module': 3,
    'start_question': 101,
    'end_question': 150,
    'output_path': 'output.docx',
    'pdf_start_page': 44,
    'pdf_end_page': 64,
    # ... other settings
}
```

## TESTING CHECKLIST
- [ ] PDF extraction successful
- [ ] Questions parsed correctly (count matches)
- [ ] Options extracted properly (all 4 options present)
- [ ] Correct answer identified
- [ ] Solutions complete and formatted
- [ ] Diagrams detected and marked
- [ ] Table centered on page
- [ ] Margins correct (2.4cm L/R, 3.5cm top)
- [ ] Column widths correct (1.5cm, 8.5cm, 3.0cm)
- [ ] Font and formatting applied
- [ ] Page breaks between questions
- [ ] Type row properly merged
- [ ] No missing/corrupted text

## CURRENT STATUS
- ✅ Core script structure complete
- ✅ Document generation working
- ✅ Table formatting perfected
- ⚠️  PDF parsing needs customization per PDF format
- ⚠️  Diagram detection needs refinement

## NEXT STEPS
1. Analyze specific PDF format
2. Write custom parsing logic for that PDF
3. Test on sample questions
4. Handle edge cases
5. Batch process multiple question ranges

## NOTES FOR AI ASSISTANT
- User has multiple PDFs from different sources
- Each PDF may have slightly different format
- Need flexible parsing that can adapt
- Quality is critical - this is client work
- Diagrams are important - don't skip them
- Solution text must be preserved exactly as in PDF
- Hindi/regional language text should be handled properly

## EXAMPLE QUESTION FORMAT IN PDF
```
101. When the object making the sound is moving
towards you, the frequency goes up due to the
waves getting pushed more tightly together.
The opposite happens when the object moves
away from you and the pitch goes down. This
phenomenon is called.
(a) Band width
(b) Doppler effect
(c) Sound refraction
(d) Vibrations
Ans. (b) : The Doppler effect or Doppler shift is the
change in frequency of a wave in relation to an observer
who is moving relative to the wave source.
```

## BUSINESS CONTEXT
- Client has 100+ PDF books with questions
- Each book: 500-2000 questions
- Multiple subjects (Computer Science, Physics, Math, etc.)
- Different examination boards (KVS, CBSE, NVS, etc.)
- Recurring work - need scalable solution
- Future: Web application for self-service

---

**When you receive this prompt, your task is to:**
1. Understand the complete document structure
2. Help improve the PDF parsing logic
3. Handle edge cases in question format
4. Ensure output quality matches specifications
5. Suggest optimizations and improvements
