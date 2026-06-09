import json
import os
from typing import Dict, List, Set

from app.config import DEFAULT_EXPERIMENT_KEYS, PROJECT_ROOT

DATA_FILE = PROJECT_ROOT / "data" / "data.json"


def load_experiment_keys() -> Set[str]:
    raw = os.getenv("EXPERIMENT_KEYS", "").strip()
    if not raw:
        return set(DEFAULT_EXPERIMENT_KEYS)
    keys = {part.strip() for part in raw.split(",") if part.strip()}
    return keys or set(DEFAULT_EXPERIMENT_KEYS)


def load_experiment_data() -> Dict[str, object]:
    if not DATA_FILE.exists():
        return {"reading_material": "", "questions": []}

    raw_obj = None
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            raw_text = DATA_FILE.read_text(encoding=encoding)
            raw_obj = json.loads(raw_text)
            break
        except Exception:
            continue

    if not isinstance(raw_obj, dict):
        return {"reading_material": "", "questions": []}

    reading_material = str(raw_obj.get("reading_material", "")).strip()
    questions: List[Dict[str, str]] = []

    flat_questions = raw_obj.get("questions", [])
    if isinstance(flat_questions, list):
        for q_index, item in enumerate(flat_questions, start=1):
            if not isinstance(item, dict):
                continue

            qid = str(item.get("question_id", f"Q{q_index}")).strip()
            question_type = str(item.get("question_type", "")).strip()
            question_text = str(item.get("question", "")).strip()
            options = item.get("options", {})
            answer_key = str(item.get("answer", "")).strip()
            explanation = str(item.get("explanation", "")).strip()
            feedback = item.get("feedback", {})

            option_choices: List[str] = []
            answer_text = answer_key
            if isinstance(options, dict):
                for opt_key, opt_val in options.items():
                    k = str(opt_key).strip()
                    v = str(opt_val).strip()
                    option_choices.append(f"{k}. {v}")
                if answer_key in options:
                    answer_text = f"{answer_key}. {str(options[answer_key]).strip()}"

            normalized_feedback = {}
            if isinstance(feedback, dict):
                normalized_feedback = {
                    str(key).strip(): str(value).strip()
                    for key, value in feedback.items()
                    if str(key).strip()
                }

            questions.append(
                {
                    "block_name": question_type or "问答题",
                    "question_type": question_type,
                    "question_id": qid,
                    "question": question_text,
                    "choices": option_choices,
                    "answer_key": answer_key,
                    "answer_text": answer_text,
                    "explanation": explanation,
                    "feedback": normalized_feedback,
                    "has_standard_answer": question_type != "模糊决策",
                }
            )

    blocks = raw_obj.get("blocks", [])
    if isinstance(blocks, list):
        for block_index, block in enumerate(blocks, start=1):
            if not isinstance(block, dict):
                continue

            block_name = str(block.get("block_name", f"Block{block_index}")).strip()
            block_questions = block.get("questions", [])
            if not isinstance(block_questions, list):
                continue

            for q_index, item in enumerate(block_questions, start=1):
                if not isinstance(item, dict):
                    continue

                qid = str(item.get("question_id", f"Q{q_index}")).strip()
                question_text = str(item.get("question", "")).strip()
                options = item.get("options", {})
                answer_key = str(item.get("answer", "")).strip()
                explanation = str(item.get("explanation", "")).strip()

                option_choices: List[str] = []
                answer_text = answer_key
                if isinstance(options, dict):
                    for opt_key, opt_val in options.items():
                        k = str(opt_key).strip()
                        v = str(opt_val).strip()
                        option_choices.append(f"{k}. {v}")
                    if answer_key in options:
                        answer_text = f"{answer_key}. {str(options[answer_key]).strip()}"

                questions.append(
                    {
                        "block_name": block_name,
                        "question_id": qid,
                        "question": question_text,
                        "choices": option_choices,
                        "answer_key": answer_key,
                        "answer_text": answer_text,
                        "explanation": explanation,
                    }
                )

    return {
        "reading_material": reading_material,
        "questions": questions,
    }


VALID_EXPERIMENT_KEYS = load_experiment_keys()
EXPERIMENT_DATA = load_experiment_data()
READING_MATERIAL = str(EXPERIMENT_DATA.get("reading_material", ""))
QUESTION_BANK = EXPERIMENT_DATA.get("questions", [])
