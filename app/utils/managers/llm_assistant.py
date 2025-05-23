import os
import yaml
import json
from typing import Dict, Any
from groq import Groq, APIConnectionError, APITimeoutError,BadRequestError
from pathlib import Path

from app.utils.logger import external_apis_logger
from app.config import assistant_config_folder ,app_folder
from app.utils.exceptions import AssistantError
from dataclasses import dataclass

@dataclass
class LlmPenalty:
    response :str 
    score :float=None


class LLMAssistant:
    """
    Handles LLM interactions for penalty scoring with minimal code repetition.
    """
    
    def __init__(self, config_path: str = "llm_config.yaml"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.logger = external_apis_logger
        self.config = self._load_config(Path(assistant_config_folder) / config_path)
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load YAML config with proper error handling
        """
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            self.logger.info("Loaded LLM config from %s", config_path.relative_to(app_folder))
            return config
        except Exception as e:
            self.logger.error("Config load failed: %s", str(e))
            raise AssistantError("Configuration loading failed") from e
        
    def get_response(self, messages, model, response_format='json_object', temperature=0.3):
        """
        Sends a message to the LLM model and returns the response.

        Args:
            messages (list): A list of message dicts in the format expected by the model.
            model (str): The model name (e.g., 'llama3-70b-8192').
            response_format (str, optional): The desired output format. Default is 'json_object'.
            temperature (float, optional): Sampling temperature for the response. Default is 0.3.

        Returns:
            object or None: The raw response object if successful, or None if an error occurs.
        """
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=model,
                response_format={"type": response_format},
                temperature=temperature
            )
            return response
        except BadRequestError as e:
            self.logger.warning("LLM API request failed: %s", str(e))
            return None


    def _call_llm(self, prompt_key: str, variables: Dict[str, Any],model=None) -> Dict[str, Any]:
        """
        Make LLM API call with configured prompts and variables.
        
        Args:
            prompt_key: Key from config to identify the prompt template
            variables: Dictionary of variables to inject into the prompt
            
        Returns:
            Parsed JSON response from LLM
        """
        try:
            prompt_config = self.config["prompts"][prompt_key]
            if not model:
                model = prompt_config.get("model", self.config["default_model"]) 
            
            messages = [
                {"role": "system", "content": prompt_config["system_prompt"]},
                {"role": "user", "content": prompt_config["user_prompt"].format(**variables)}
            ]
            self.logger.debug(messages)
            self.logger.debug("LLM request - model=%s, prompt=%s", model, prompt_key)
       
            for i in range(3):
                response = self.get_response(messages,model)
                if response:
                    break 
            if not response:
                return None 
            
            content = response.choices[0].message.content
            result = json.loads(content)
            self.logger.debug("LLM response - %s", result)
            return result
            
        except json.JSONDecodeError as e:
            error = AssistantError(
                message="Invalid LLM response format",
                status_code=502,
                prompt_key=prompt_key,
                model=model
            )
            self.logger.error("JSON decode failed: %s", error.to_response())
            raise error
            
        except (APITimeoutError, APIConnectionError) as e:
            error = AssistantError(
                message=f"LLM API connection failed: {str(e)}",
                status_code=503
            )
            self.logger.error("API connection failed")
            raise error
            
        except Exception as e:
            error = AssistantError(
                message=f"Unexpected LLM error: {str(e)}",
                status_code=500
            )
            self.logger.error("Unexpected error: %s", str(e))
            raise error
    
    def _calculate_penalty(self, penalty_type: str,model:str=None ,**variables) -> float:
       
        response = self._call_llm(penalty_type, model=model,variables=variables)
        if not response:
            return None 
        
        score = float(response["penalty_score"])
        
        if not 0 <= score <= 1:
            self.logger.error("Invalid penalty score: %s", score)
            raise ValueError("Penalty score must be 0-1")
            
        self.logger.info(
            "%s penalty calculated: %.2f",
            penalty_type.replace('_', ' ').title(),
            score
        )
        return LlmPenalty(response,score)
    
    def calculate_late_penalty_score(
        self,
        start_time: str,
        completion_time: str,
        scheduled_duration: int,
        reason: str,
        task_difficulty: float,
        task_description: str,
        model:str=None,
        test=False
    ) -> LlmPenalty:
        """
        Calculate late penalty score (0-1) using LLM.
        
        Args:
            start_time: Scheduled start time (ISO format)
            completion_time: Actual completion time (ISO format)
            scheduled_duration: Scheduled duration in minutes
            task_difficulty: Difficulty multiplier (1.0-2.0)
            task_description: Description of the task
            
        Returns:
            Penalty score between 0 (no penalty) and 1 (max penalty)
        """
        if test:
            return None 
        print(start_time,completion_time,scheduled_duration,reason)
        return self._calculate_penalty(
            "late_penalty",
            start_time=start_time,
            completion_time=completion_time,
            scheduled_duration=scheduled_duration,
            reason=reason,
            task_difficulty=task_difficulty,
            task_description=task_description,
            model=model
        )
    
    def calculate_skip_penalty_score(
        self,
        reason: str,
        task_difficulty: float,
        task_description: str,
        model=None 
        ) -> float:
        """
        Calculate skip penalty score (0-1) using LLM.
        
        Args:
            reason: Reason for skipping
            task_difficulty: Difficulty multiplier (1.0-2.0)
            task_description: Description of the task

        Returns:
            Penalty score between 0 (no penalty) and 1 (max penalty)
        """
        return self._calculate_penalty(
            "skip_penalty",
            reason=reason,
            task_difficulty=task_difficulty,
            task_description=task_description,
            model=model
        )