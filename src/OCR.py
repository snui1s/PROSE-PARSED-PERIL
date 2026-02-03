import easyocr
import fitz
import os
import csv


def init_csv(csv_path):
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "resumename", "ocr_result"])
    return 1


def process_all_resumes(resume_dir, csv_path, ocr_mode="auto"):
    next_id = init_csv(csv_path)

    files = [f for f in os.listdir(resume_dir) if f.endswith(".pdf")]
    if not files:
        print("No PDF files found.")
        return

    reader = None
    if ocr_mode in ["auto", "force_ocr"]:
        print("Initializing EasyOCR (this takes a moment)...")
        reader = easyocr.Reader(["th", "en"])

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "resumename", "ocr_result"])

        for filename in files:
            pdf_path = os.path.join(resume_dir, filename)
            print(f"Processing ID {next_id}: {filename}")

            try:
                doc = fitz.open(pdf_path)
                full_text = ""
                should_use_ocr = False

                # 1. Determine if we skip text extraction
                if ocr_mode == "force_ocr":
                    should_use_ocr = True
                else:
                    # Try text extraction (PyMuPDF)
                    for page in doc:
                        full_text += page.get_text() + "\n"

                    # If auto, check quality
                    if ocr_mode == "auto" and len(full_text.strip()) < 50:
                        print(
                            f"  > Text too short/empty. Switching to OCR for {filename}..."
                        )
                        should_use_ocr = True

                # 2. Execute OCR if flagged
                if should_use_ocr:
                    full_text = ""  # Reset text
                    for page in doc:
                        # Zoom = 2 (2x resolution = 144 dpi) for better OCR
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        temp_img = f"temp_ocr_{next_id}.png"
                        pix.save(temp_img)

                        if reader:
                            result = reader.readtext(temp_img, detail=0)
                            full_text += " ".join(result) + "\n"

                        if os.path.exists(temp_img):
                            os.remove(temp_img)

                # Clean up text slightly
                full_text = full_text.strip()

                writer.writerow([next_id, filename, full_text])
                f.flush()
                print(f"Done.")

                next_id += 1
                doc.close()
            except Exception as e:
                print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    RESUME_DIR = "resumes"
    CSV_DB = "ocr_results.csv"

    if os.path.exists(RESUME_DIR):
        process_all_resumes(RESUME_DIR, CSV_DB)
        print(f"\nOCR completed. Data saved to {CSV_DB}")
    else:
        print(f"Directory '{RESUME_DIR}' not found.")
