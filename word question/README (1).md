# KVS PGT Document Generator

Automated tool to convert PDF question papers into formatted Word documents (.docx) with precise table structure.

## 📋 Features

- ✅ Extract questions from PDF files
- ✅ Generate formatted Word documents
- ✅ Customizable formatting (margins, fonts, column widths)
- ✅ Center-aligned tables
- ✅ Automatic diagram detection
- ✅ Bilingual text support
- ✅ Batch processing capability

## 🛠️ Installation

### Prerequisites

**1. Python 3.7+**
```bash
# Check Python version
python3 --version
```

**2. Install Python dependencies**
```bash
# Install python-docx
pip install python-docx

# Or using pip3
pip3 install python-docx
```

**3. Install pdftotext (poppler-utils)**

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**On macOS:**
```bash
brew install poppler
```

**On Windows:**
- Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
- Extract and add `bin` folder to PATH
- Or use WSL (Windows Subsystem for Linux)

**Verify installation:**
```bash
pdftotext -v
```

## 📁 Project Structure

```
kvs-document-generator/
├── kvs_document_generator.py   # Main script
├── PROMPT_FOR_AI.md            # Detailed prompt for AI assistants
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── sample_questions.py         # Sample question data (for testing)
└── pdfs/                       # Place your PDF files here
    └── your_question_paper.pdf
```

## 🚀 Quick Start

### Step 1: Configure the script

Open `kvs_document_generator.py` and modify the `CONFIG` section:

```python
CONFIG = {
    # PDF file path
    'pdf_path': 'pdfs/your_question_paper.pdf',
    
    # Year and module
    'year': 2013,
    'module': 3,
    
    # Question range
    'start_question': 101,
    'end_question': 150,
    
    # Output file path
    'output_path': 'output/KVS_PGT_2013_Q101-150.docx',
    
    # PDF page range (where questions are located)
    'pdf_start_page': 44,
    'pdf_end_page': 64,
    
    # Other settings (margins, fonts, etc.) - usually don't need to change
}
```

### Step 2: Run the script

```bash
python3 kvs_document_generator.py
```

### Step 3: Check output

- Word document will be saved to path specified in `output_path`
- Console will show progress and any diagrams detected
- Open the document in Microsoft Word to verify formatting

## ⚙️ Configuration Options

### PDF Settings
- `pdf_path`: Path to input PDF file
- `pdf_start_page`: First page number to extract
- `pdf_end_page`: Last page number to extract

### Question Settings
- `year`: Examination year
- `module`: Module/section number
- `start_question`: First question number
- `end_question`: Last question number

### Output Settings
- `output_path`: Where to save the Word document

### Page Margins (in cm)
- `margin_left`: 2.4
- `margin_right`: 2.4
- `margin_top`: 3.5
- `margin_bottom`: 2.4

### Column Widths (in cm)
- `label_column_width`: 1.5 (Question/Type/Option labels)
- `content_column_width`: 8.5 (Main content)
- `right_column_width`: 3.0 (correct/incorrect)

### Font Settings
- `font_name`: 'Times New Roman'
- `font_size`: 14 (in points)
- `font_bold`: True

### Cell Padding (in dxa, 20 dxa = 1 point)
- `cell_padding_top`: 120
- `cell_padding_bottom`: 120
- `cell_padding_left`: 100
- `cell_padding_right`: 100

### Marks
- `marks_correct`: '1'
- `marks_incorrect`: '0.25'

## 🔧 Customization

### For Different PDF Formats

The `parse_questions_from_pdf_text()` function needs to be customized for your specific PDF format.

**Current implementation is a TEMPLATE.** You need to:

1. **Analyze your PDF text:**
   ```bash
   # Extract and save PDF text to file
   pdftotext -f 44 -l 64 -raw your_pdf.pdf output.txt
   
   # Open output.txt and study the format
   ```

2. **Write parsing logic:**
   ```python
   def parse_questions_from_pdf_text(pdf_text, start_q, end_q):
       questions = []
       
       # Example: Split by question number
       question_pattern = r'(\d+)\.\s+(.*?)(?=\d+\.|$)'
       matches = re.findall(question_pattern, pdf_text, re.DOTALL)
       
       for q_num, q_text in matches:
           # Parse question, options, answer, solution
           question_data = {
               'question': [...],
               'options': [...],
               'correct_idx': 0,
               'solution': [...],
               'has_diagram': False
           }
           questions.append(question_data)
       
       return questions
   ```

3. **Test thoroughly:**
   - Start with 2-3 questions
   - Verify all text extracted correctly
   - Check option parsing
   - Verify correct answer detection
   - Check solution completeness

### Adding New Features

**1. Custom table styles:**
```python
# In create_question_table() function
table.style = 'Your Custom Style'
```

**2. Different question types:**
```python
# Add support for True/False, Multiple Select, etc.
CONFIG['question_type'] = 'multiple_choice'  # or 'true_false', 'multi_select'
```

**3. Image insertion:**
```python
from docx.shared import Inches
# Add to question cell:
paragraph.add_run().add_picture('diagram.png', width=Inches(2.0))
```

## 🐛 Troubleshooting

### Issue: "pdftotext: command not found"
**Solution:** Install poppler-utils (see Installation section)

### Issue: "ModuleNotFoundError: No module named 'docx'"
**Solution:** 
```bash
pip install python-docx
# NOT: pip install docx (this is a different package!)
```

### Issue: Tables not centered
**Solution:** Check if `WD_TABLE_ALIGNMENT.CENTER` is being applied. Update python-docx if needed:
```bash
pip install --upgrade python-docx
```

### Issue: Unicode errors with special characters
**Solution:** 
```python
# In PDF extraction, ensure UTF-8 encoding
result = subprocess.run(..., text=True, encoding='utf-8')
```

### Issue: Incorrect question parsing
**Solution:** 
1. Extract PDF text manually: `pdftotext -raw input.pdf output.txt`
2. Study the format in `output.txt`
3. Adjust regex patterns in `parse_questions_from_pdf_text()`
4. Test with small sample first

### Issue: Missing content in output
**Solution:**
- Check if PDF page range is correct
- Verify question number range
- Check for pagination issues in PDF
- Some PDFs have text as images (OCR needed)

## 📊 Batch Processing

To process multiple question ranges:

```python
# Create a batch configuration
batches = [
    {'start': 101, 'end': 125, 'output': 'Q101-125.docx'},
    {'start': 126, 'end': 150, 'output': 'Q126-150.docx'},
    {'start': 151, 'end': 175, 'output': 'Q151-175.docx'},
]

for batch in batches:
    CONFIG['start_question'] = batch['start']
    CONFIG['end_question'] = batch['end']
    CONFIG['output_path'] = batch['output']
    main()  # Run generation
```

## 📝 Output Format

### Table Structure (per question)
```
┌──────────┬────────────────────────────────────┬──────────────┐
│ Question │ Question text here...              │              │
│          │ (merged columns 2-3)               │              │
├──────────┼────────────────────────────────────┴──────────────┤
│ Type     │ Multiple_choice                                   │
│          │ (merged columns 2-3)                              │
├──────────┼────────────────────────────────────┬──────────────┤
│ Option   │ Option A text                      │ correct      │
├──────────┼────────────────────────────────────┼──────────────┤
│ Option   │ Option B text                      │ incorrect    │
├──────────┼────────────────────────────────────┼──────────────┤
│ Option   │ Option C text                      │ incorrect    │
├──────────┼────────────────────────────────────┼──────────────┤
│ Option   │ Option D text                      │ incorrect    │
├──────────┼────────────────────────────────────┴──────────────┤
│ Solution │ Solution explanation here...                      │
│          │ (merged columns 2-3)                              │
├──────────┼────────────────────────────────────┬──────────────┤
│ Marks    │ 1                                  │ 0.25         │
└──────────┴────────────────────────────────────┴──────────────┘
```

## 🤝 Contributing

For client work customizations or issues:
1. Document the PDF format
2. Provide sample pages
3. Specify exact requirements
4. Test thoroughly before production use

## 📄 License

Proprietary - Client Work

## 🔮 Future Enhancements

See `WEB_APPLICATION_VISION.md` for planned web application features.

## 📧 Support

For issues or questions, please provide:
- PDF sample (1-2 pages)
- Expected output format
- Error messages (if any)
- Python and dependency versions

---

**Happy Document Generating! 🎉**
