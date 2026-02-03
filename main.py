import os
from src.OCR import process_all_resumes
from src.judge import main_evaluation_loop


import argparse


def main():
    parser = argparse.ArgumentParser(description="Resume Judge AI")
    parser.add_argument(
        "--mode",
        choices=["auto", "text", "ocr", "skip"],
        help="Run without menu: auto (smart), text (fast), ocr (scanned), skip (judge only)",
    )
    args = parser.parse_args()

    RESUME_DIR = "resumes"
    OCR_CSV = "ocr_results.csv"

    ocr_mode = "auto"
    run_ocr = True

    # Check if passing arguments (Level 2 Automation)
    if args.mode:
        print(f"--- RUNNING IN AUTOMATION MODE: {args.mode.upper()} ---")
        if args.mode == "text":
            ocr_mode = "force_text"
        elif args.mode == "ocr":
            ocr_mode = "force_ocr"
        elif args.mode == "skip":
            run_ocr = False
    else:
        # Interactive Menu (Level 1)
        print("=========================================")
        print("      RESUME JUDGE AI - MAIN MENU        ")
        print("=========================================")
        print("1. Run Complete Pipeline (Auto Mode - Recommended)")
        print("   -> Tries Text extraction first, falls back to OCR if empty.")
        print("2. Run Complete Pipeline (Force Text / PyMuPDF)")
        print("   -> Fast. Best for digital PDFs. Ignores images.")
        print("3. Run Complete Pipeline (Force OCR / EasyOCR)")
        print("   -> Slow. Best for scanned PDFs/Images. Forces OCR on everything.")
        print("4. Run Judge Only (Skip OCR Step)")
        print("5. Exit")
        print("-----------------------------------------")
        print(
            "[TIP] Want to run OFFLINE with Ollama? Check 'src/judge.py' for instructions."
        )
        print("=========================================")

        choice = input("Select an option (1-5) [Default: 1]: ").strip()

        if choice == "2":
            ocr_mode = "force_text"
        elif choice == "3":
            ocr_mode = "force_ocr"
        elif choice == "4":
            run_ocr = False
        elif choice == "5":
            print("Exiting...")
            return
        else:
            ocr_mode = "auto"

    if run_ocr:
        print(f"\n=== STEP 1: RUNNING OCR PROCESS (Mode: {ocr_mode}) ===")

        # Case 1: Folder doesn't exist
        if not os.path.exists(RESUME_DIR):
            os.makedirs(RESUME_DIR)
            print(
                f"\n[INFO] Directory '{RESUME_DIR}' was missing, so I created it for you."
            )
            print(
                f"Please put your PDF resumes into the '{RESUME_DIR}' folder and run me again! Thank you.\n"
            )
            return

        files = [f for f in os.listdir(RESUME_DIR) if f.endswith(".pdf")]

        # Case 2: Folder exists but is empty (no PDFs)
        if not files:
            print(
                f"\n[WARNING] There are NO resumes (PDF files) in the '{RESUME_DIR}' folder."
            )
            print(
                f"Please copy your resume files into '{os.path.abspath(RESUME_DIR)}' and retry.\n"
            )

            # Check if we can fall back to existing data
            if os.path.exists(OCR_CSV):
                print(
                    f"However, I found an existing '{OCR_CSV}'. Moving to evaluation using old data...\n"
                )
            else:
                return  # Stop execution if no new files AND no old data
        else:
            # Case 3: Resumes found -> Process them
            process_all_resumes(RESUME_DIR, OCR_CSV, ocr_mode=ocr_mode)
            print("\nOCR Step Completed.\n")

    print("=== STEP 2: RUNNING AI EVALUATION (JUDGE) ===")
    main_evaluation_loop()
    print("\nAI Evaluation Step Completed.")
    print("You can check the final results in 'judge_results.csv'")


if __name__ == "__main__":
    main()
