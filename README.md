# Resume Judge AI Agent

An automated resume evaluation system using AI Agents to analyze and score candidates against a Job Description.

## Key Features

1. **Hybrid OCR:** Direct text extraction from PDFs or OCR (EasyOCR) for scanned images.
2. **AI Agent Workflow:** Uses a Reviewer and Auditor (QC) node-based graph for high-accuracy evaluations.
3. **Thai Language Support:** Analysis and summaries are provided in Thai.

## Prerequisites

1. **Python 3.10+**
2. **OpenAI API Key:** Create a `.env` file in the root directory:

   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Project Prep:**
   - Place your resume PDF files in the `resumes/` folder.
   - Edit `job_description.txt` with your desired job requirements.

## Quick Start

1. **Prepare:**
   - Put your Resume PDFs into the `resumes` folder.
   - Paste your job requirements into `job_description.txt`.
   - (First time only) Create a `.env` file and add `OPENAI_API_KEY=sk-...`.

2. **Run:**

   ```powershell
   python main.py
   ```

   _Then press `1` and Enter._

3. **Check Results:**
   - The system will generate both **`judge_results.csv`** and **`judge_results.xlsx`**.
   - Open the **Excel** file to see scores and detailed feedback.

---

## How to Use (Detailed)

### 1. Interactive Mode (Menu) - Best for Beginners

Simply run the main script. The system will guide you through a menu to verify files, choose OCR modes, and start the evaluation.

```powershell
# Using uv (Recommended)
uv run main.py

# OR Using standard Python
python main.py
```

**You will see a menu like this:**

```text
1. Run Complete Pipeline (Auto Mode) -> Recommended. Smartly chooses between Text/OCR.
2. Run Complete Pipeline (Force Text) -> Fast. Ignores images (good for digital PDFs).
3. Run Complete Pipeline (Force OCR)  -> Slow. Forces image scanning (good for scans).
4. Run Judge Only (Skip OCR Step)     -> Skip extracting text, just re-evaluate existing CSV.
5. Exit
```

### 2. Advanced Mode (Automation / CLI) - Best for Scripts

You can skip the menu by passing arguments. This is perfect for setting up automated tasks or cron jobs.

| Command                      | Description                                         |
| :--------------------------- | :-------------------------------------------------- |
| `python main.py --mode auto` | **Standard.** Auto-detects text vs scanned PDF.     |
| `python main.py --mode text` | **Fastest.** Forces text extraction only (PyMuPDF). |
| `python main.py --mode ocr`  | **Most Correct.** Forces OCR on every file (Slow).  |
| `python main.py --mode skip` | **Judge Only.** Skips OCR processing completely.    |

**Example:**

```powershell
uv run main.py --mode auto
```

### 3. File Handling Logic (Intelligent Check)

- If the `resumes/` folder is missing, the script will **create it for you** and ask you to put files in.
- If the folder is empty, it will warn you.
- If no PDF files are found but a CSV exists, it will offer to use the old data.

## Key File Structure

- `main.py`: Orchestrator script (OCR -> Judge).
- `OCR.py`: Text extraction and OCR logic.
- `judge.py`: The AI Agent logic (Reviewer & Auditor).
- `ocr_results.csv`: Raw extracted text from resumes.
- `judge_results.csv`: **Final evaluation results (Score + Analysis)**.
- `job_description.txt`: Input file for job requirements.

## Viewing Results

Open **`judge_results.csv`** in Excel:

- **Score:** 0-10 rating.
- **Evaluation:** Detailed strengths and weaknesses in Thai.

## Privacy & Configuration

The default model is `gpt-4o-mini`. While this requires an internet connection to OpenAI, your resume data is only processed for the evaluation.

### 100% Offline Usage (Ollama)

If you require maximum data privacy and want to run the system **100% offline**, you can switch to **Ollama**:

1. Install [Ollama](https://ollama.com/).
2. Pull a local model: `ollama pull llama3.2`.
3. In `judge.py`, switch `ChatOpenAI` to `ChatOllama`.
4. Run using: `uv run main.py`.

_Note: For complete offline OCR, ensure you have run the program at least once with an internet connection to download the initial EasyOCR model files._
