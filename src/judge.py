import os
import csv
import pandas as pd
from datetime import datetime
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

load_dotenv()


# --- 1. State Definition ---
class GraphState(TypedDict):
    resume_text: str
    job_description: str
    reviewer_output: str
    feedback_history: List[str]
    status: str  # "PASS" or "FAIL"
    retry_count: int


# --- 2. Node Logic ---


class ResumeJudgeGraph:
    def __init__(self, model_name="gpt-4o-mini"):
        # Look for either key name
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAPI_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY (or OPENAPI_KEY) not found in environment variables."
            )

        # ==============================================================================
        # [GUIDE] HOW TO SWITCH TO OLLAMA (OFFLINE MODE 100%)
        # ==============================================================================
        # 1. Install Ollama app from https://ollama.com
        # 2. Pull a model in terminal: `ollama pull llama3.2`
        # 3. Import at the top: `from langchain_ollama import ChatOllama`
        # 4. Comment out the ChatOpenAI line below and un-comment the ChatOllama line:
        #
        # self.llm = ChatOllama(model="llama3.2", temperature=0.4)
        # ==============================================================================

        self.llm = ChatOpenAI(model=model_name, temperature=0.4, api_key=api_key)

    def node_1_reviewer(self, state: GraphState):
        """
        Node 1: The Reviewer
        Analyzes resume vs JD. Adjusts based on feedback.
        """
        print(
            f"\n... Node 1 (Reviewer) is thinking (Attempt {state['retry_count'] + 1})..."
        )

        history_text = ""
        if state["feedback_history"]:
            history_text = (
                "\\n\\n--- PREVIOUS AUDITOR FEEDBACK (FIX THESE ISSUES) ---\\n"
            )
            for i, feedback in enumerate(state["feedback_history"]):
                history_text += f"Round {i+1} Feedback: {feedback}\\n"

        system_msg = """
        Role: You are a Professional Talent Acquisition Partner specializing in "Potential-Based Hiring."
        Task: Evaluate the candidate's Resume against the JD by identifying real, relevant connections between their past experience and the role's requirements.

        Evaluation Guidelines:
        1. **Evidence-Based Transferable Skills**: You may give partial credit ONLY for skills within the same family (e.g., Vue for React, Chemical Engineering Data Analysis for General Data Analysis). DO NOT give credit for completely unrelated fields (e.g., Chemical Lab work does not translate to Backend Coding).
        2. **Growth Mindset with Proof**: "Potential" must be backed by evidence of fast learning in the resume (e.g., certifications, rapid career progression, or self-taught projects). If there is no evidence of learning in a related field, do not assume they have it.
        3. **Realistic Constructive Feedback**: Identify gaps clearly. Frame them as areas for improvement, but be honest about the distance between the candidate's current state and the 10/10 requirements.
        4. **If a candidate is a 90% mismatch, do not try to find 'Transferable Skills' from unrelated fields. Be blunt and state: 'No relevant skills found for this role'.**
        5. **Do not translate or change headers 0, 1, and 2. Use them exactly as specified.**
        
        Output Requirements (ALWAYS RESPOND IN THAI):
        0. **Candidate Metadata**:
           - Name: [EXACT name from resume - NO TRANSLATION]
           - Email: [Email Address]
        1. Score (0-10): Be realistic. If the candidate is from a completely different industry with no relevant technical skills, the score should naturally be low (below 3).
        2. Analysis: 
           - **จุดแข็ง (Strengths):** ขีดความสามารถที่โดดเด่นและมีหลักฐานชัดเจนใน Resume
           - **ทักษะที่นำมาปรับใช้ได้ (Transferable Skills):** ทักษะที่เกี่ยวข้องทางตรรกะหรือสายงานใกล้เคียงกันเท่านั้น (ห้ามแถ)
           - **สิ่งที่ต้องพัฒนา (Gaps & Growth Areas):** ทักษะทางเทคนิคหรือประสบการณ์ที่ขาดหายไปอย่างชัดเจนเมื่อเทียบกับ JD
        
        If you receive feedback from the Auditor, adjust your analysis. Focus on real evidence, not assumptions.
        """

        user_msg = f"""
        [JOB DESCRIPTION]
        {state['job_description']}

        [RESUME TEXT]
        {state['resume_text']}
        
        {history_text}
        
        Generate your evaluation now.
        """

        response = self.llm.invoke(
            [SystemMessage(content=system_msg), HumanMessage(content=user_msg)]
        )

        return {
            "reviewer_output": response.content,
            "retry_count": state["retry_count"] + 1,
        }

    def node_2_auditor(self, state: GraphState):
        """
        Node 2: The Auditor
        Checks Reviewer output against Resume and JD.
        """
        print("\n... Node 2 (Auditor) is verifying...")

        system_msg = """
        Role: You are a Senior HR Auditor & Quality Controller.
        Task: Audit the Recruiter's evaluation to ensure it is logically sound, evidence-based, and accurately reflects the candidate's fit for the JD.

        Verification Checklist:
        1. **Logical Transferable Skills**: Check if the Recruiter missed a skill in the SAME FAMILY. If the JD asks for "Jira" but the candidate has "Asana/Trello", the Recruiter should give credit. HOWEVER, if the JD asks for "Python" and the candidate has "Chemical Engineering Research," do NOT intervene; these are NOT transferable skills.
        2. **Anti-Hallucination Check**: Did the Recruiter "invent" potential or skills not found in the Resume? If the Recruiter says "the candidate can learn Python" without any proof of coding history, you MUST FAIL the evaluation.
        3. **No-Nonsense Bias Check**: Ensure the Recruiter is not being "too nice." If a candidate lacks 90% of the core requirements, a score above 3 is illogical. FAIL the evaluation if the score is too high for a weak candidate.
        4. **If the Reviewer gives a low score (1-3) and correctly identifies that the candidate lacks almost all core requirements, you MUST return 'PASS'. Even if you think the candidate is terrible, as long as the Reviewer agrees they are terrible, the evaluation is ACCURATE.**
        
        Response Format:
        - If the evaluation is accurate, logical, and evidence-based: Return exactly "PASS".
        - If the evaluation is illogical, misses legitimate skill connections, or is UNREALISTICALLY POSITIVE: Return "FAIL: [ระบุจุดบกพร่องตามหลักการและตรรกะเป็นภาษาไทยเท่านั้น]".

        CRITICAL: All feedback must be strictly in Thai. Do not encourage "Potential" without evidence.
        """

        user_msg = f"""
        [JOB DESCRIPTION]
        {state['job_description']}

        [ORIGINAL RESUME TEXT]
        {state['resume_text']}
        
        [REVIEWER'S EVALUATION]
        {state['reviewer_output']}
        
        Verify this evaluation.
        """

        response = self.llm.invoke(
            [SystemMessage(content=system_msg), HumanMessage(content=user_msg)]
        )
        result = response.content.strip()

        status = "PASS" if result.upper() == "PASS" else "FAIL"

        # If fail, append to history
        new_history = state["feedback_history"]
        if status == "FAIL":
            print(f"!!! AUDITOR REJECTED: {result}")
            new_history = state["feedback_history"] + [result]
        else:
            print(f"\n>>> AUDITOR APPROVED <<<")

        return {"status": status, "feedback_history": new_history}

    def build_graph(self):
        workflow = StateGraph(GraphState)

        # Add Nodes
        workflow.add_node("reviewer", self.node_1_reviewer)
        workflow.add_node("auditor", self.node_2_auditor)

        # Set Entry Point
        workflow.set_entry_point("reviewer")

        # Add Edges
        workflow.add_edge("reviewer", "auditor")

        # Conditional Edge Logic
        def check_auditor_verdict(state: GraphState):
            if state["status"] == "PASS":
                return "end"
            if state["retry_count"] >= 3:
                print(
                    "\n*** Max retries reached. Returning last Reviewer output with warning. ***"
                )
                return "end"
            return "retry"

        workflow.add_conditional_edges(
            "auditor", check_auditor_verdict, {"end": END, "retry": "reviewer"}
        )

        return workflow.compile()


# Helper to load a resume from CSV
def load_resume_from_csv(csv_path, resume_id):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == str(resume_id):
                return row["ocr_result"]
    return None


def main_evaluation_loop():
    # --- Configuration ---
    csv_db = "ocr_results.csv"
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_csv = f"judge_results_{today_str}.csv"
    jd_file = "job_description.txt"

    # 1. Load JD
    if os.path.exists(jd_file):
        with open(jd_file, "r", encoding="utf-8") as f:
            job_description = f.read()
    else:
        print(f"Error: {jd_file} not found.")
        return

    # 2. Check Input Data
    if not os.path.exists(csv_db):
        print(f"Error: {csv_db} not found. Please run OCR.py first.")
        return

    # 3. Setup Graph
    judge_graph = ResumeJudgeGraph()
    app = judge_graph.build_graph()

    # 4. Prepare Output CSV
    file_exists = os.path.exists(output_csv)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_csv, mode="a", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        if not file_exists:
            writer.writerow(["date", "id", "resumename", "score", "evaluation"])

        # 5. Process all resumes
        with open(csv_db, mode="r", encoding="utf-8") as in_f:
            reader = csv.DictReader(in_f)
            import re

            def extract_score(text):
                # Try to find "Score (0-10): X" or "คะแนน: X"
                match = re.search(
                    r"(?:Score|คะแนน)\s*(?:\(0-10\))?:\s*(\d+(\.\d+)?)",
                    text,
                    re.IGNORECASE,
                )
                if match:
                    return match.group(1)
                return "N/A"

            for row in reader:
                resume_id = row["id"]
                resume_name = row["resumename"]
                resume_text = row["ocr_result"]

                print(f"\n>>> Processing ID {resume_id}: {resume_name}")

                initial_state = {
                    "resume_text": resume_text,
                    "job_description": job_description,
                    "reviewer_output": "",
                    "feedback_history": [],
                    "status": "START",
                    "retry_count": 0,
                }

                try:
                    final_state = app.invoke(initial_state)

                    evaluation_text = final_state["reviewer_output"]
                    score = extract_score(evaluation_text)
                    # status = final_state["status"] # Not used in output anymore

                    writer.writerow(
                        [current_date, resume_id, resume_name, score, evaluation_text]
                    )
                    out_f.flush()  # Save progress immediately

                    print(f"Done. Score: {score}")

                except Exception as e:
                    print(f"Error evaluating ID {resume_id}: {e}")

    print(f"\nEvaluation completed. Results saved to {output_csv}")

    # 6. Generate Excel version
    try:
        excel_path = output_csv.replace(".csv", ".xlsx")
        df = pd.read_csv(output_csv)
        df.to_excel(excel_path, index=False)
        print(f"Excel version saved to {excel_path}")
    except Exception as e:
        print(f"Error generating Excel file: {e}")


if __name__ == "__main__":
    main_evaluation_loop()
