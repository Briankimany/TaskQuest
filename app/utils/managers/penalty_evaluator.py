"""
Domain evaluator for LLM-generated penalty scores and judge reviews.

Owns what prompts exist, what variables they need, and how to validate and
interpret the assistant's answer into business objects (``LlmPenalty`` / judge
metrics). Transport is delegated to an injected ``AIAssistant`` — this module
never does HTTP or retries itself.

Prompt templates come from ``llm_prompts.yaml`` (system/user templates per
key). Transport config (model, base_url) lives with the assistant.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from app.utils.logger import external_apis_logger
from app.config import assistant_config_folder
from app.utils.exceptions import AssistantError
from .ai_assistant import AIAssistant


@dataclass
class LlmPenalty:
    response: str
    score: float = None

def clamp(value):
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 0

class PenaltyEvaluator:
    """Owns penalty/judge prompt logic, delegating transport to an AIAssistant."""

    def __init__(self, assistant: AIAssistant, prompts_config_path: str = "llm_prompts.yaml"):
        self.assistant = assistant
        self.logger = external_apis_logger
        self.prompts = self._load_prompts(Path(assistant_config_folder) / prompts_config_path)

    def _load_prompts(self, prompts_path: Path) -> dict:
        try:
            with open(prompts_path) as f:
                config = yaml.safe_load(f)
            return config.get("prompts", {})
        except Exception as e:
            self.logger.error("Prompts config load failed: %s", str(e))
            raise AssistantError("Prompts configuration loading failed") from e

    # ── prompt assembly ──
    def _build_messages(self, prompt_key: str, variables: dict, model: str = None):
        prompt_config = self.prompts.get(prompt_key)
        if not prompt_config:
            raise AssistantError(f"Unknown prompt key: {prompt_key}")
        system_prompt = prompt_config["system_prompt"]
        user_prompt = prompt_config["user_prompt"].format(**variables)
        return system_prompt, user_prompt

    def _calculate_penalty(self, penalty_type: str, model: str = None, **variables) -> Optional[LlmPenalty]:
        """Ask the assistant for a penalty score and validate the 0-1 domain rule."""
        response = self.assistant.complete(*self._build_messages(penalty_type, variables, model), model=model)
        if response is None:
            return None

        try:
            score = float(response["penalty_score"])
        except (KeyError, TypeError, ValueError) as e:
            self.logger.warning("LLM response missing or invalid penalty_score (model=%s): %s", model, e)
            return None

        if not 0 <= score <= 1:
            self.logger.error("Invalid penalty score: %s", score)
            raise ValueError("Penalty score must be 0-1")

        self.logger.info(
            "%s penalty calculated: %.2f",
            penalty_type.replace('_', ' ').title(),
            score
        )
        return LlmPenalty(response, score)

    def calculate_late_penalty_score(
        self,
        start_time: str,
        completion_time: str,
        scheduled_duration: int,
        reason: str,
        task_difficulty: float,
        task_description: str,
        model: str = None,
    ) -> Optional[LlmPenalty]:
        """
        Calculate late penalty score (0-1) using LLM.

        Args:
            start_time: Scheduled start time (ISO format)
            completion_time: Actual completion time (ISO format)
            scheduled_duration: Scheduled duration in minutes
            task_difficulty: Difficulty multiplier (1.0-2.0)
            task_description: Description of the task

        Returns:
            Penalty score between 0 (no penalty) and 1 (max penalty), or None
            when the assistant could not be reached.
        """
        return self._calculate_penalty(
            "late_penalty",
            start_time=start_time,
            completion_time=completion_time,
            scheduled_duration=scheduled_duration,
            reason=reason,
            task_difficulty=task_difficulty,
            task_description=task_description,
            model=model,
        )

    def calculate_skip_penalty_score(
        self,
        reason: str,
        task_difficulty: float,
        task_description: str,
        model=None,
    ) -> Optional[LlmPenalty]:
        """
        Calculate skip penalty score (0-1) using LLM.

        Args:
            reason: Reason for skipping
            task_difficulty: Difficulty multiplier (1.0-2.0)
            task_description: Description of the task

        Returns:
            Penalty score between 0 (no penalty) and 1 (max penalty), or None
            when the assistant could not be reached.
        """
        return self._calculate_penalty(
            "skip_penalty",
            reason=reason,
            task_difficulty=task_difficulty,
            task_description=task_description,
            model=model,
        )

    def evaluate_judge_review(
        self,
        task_name: str,
        task_status: str,
        reason: str,
        penalty: int,
        discipline: int,
        dispute_reason: str = "",
        model: str = None,
    ) -> Optional[dict]:
        """Ask the assistant for a judge review and validate its metric shape.

        Returns a dict like {"validity": 0-100, "responsibility": 0-100,
        "consistency": 0-100, "explanation": "..."}, or None when the assistant
        is unreachable. Values are clamped to the 0-100 domain rule.
        """
        response = self.assistant.complete(
            *self._build_messages(
                "judge_review",
                {
                    "task_name": task_name,
                    "task_status": task_status,
                    "reason": reason or "",
                    "penalty": penalty or 0,
                    "discipline": discipline or 0,
                    "dispute_reason": dispute_reason or "",
                },
                model,
            ),
            model=model,
        )
        if response is None:
            return None



        return {
            "validity": clamp(response.get("validity")),
            "responsibility": clamp(response.get("responsibility")),
            "consistency": clamp(response.get("consistency")),
            "explanation": str(response.get("explanation", "")),
        }