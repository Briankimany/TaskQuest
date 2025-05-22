from pathlib import Path
import sys 
sys.path.append(str(Path().cwd().parent.parent.absolute()))

from time import sleep
from app.config import DATE_PARSING_STRING ,TIME_DATE_SEPARATOR,TIME_PARSING_STRING
from app.utils.managers.llm_assistant import * 
from datetime import datetime,timedelta ,time
import json

from concurrent.futures import ThreadPoolExecutor ,as_completed
from tqdm.auto import tqdm 
from groq import BadRequestError

assistant = LLMAssistant()

starting = datetime.combine(datetime.now(),time(hour=13))
end = starting + timedelta(hours=4)

P = DATE_PARSING_STRING+TIME_DATE_SEPARATOR+TIME_PARSING_STRING
def format_time(date_time:datetime):
    return date_time.strftime(P)



test_matrix = {
    "Revise Organic Chemistry": {
        "on_time": {
            "valid_reason": "Started and finished exactly as planned.",
            "weak_reason": "Just decided to follow my routine for once.",
            "invalid_reason": "Whatever, I did it, no big deal."
        },
        "late": {
            "valid_reason": "I had to help my younger sibling with urgent homework.",
            "weak_reason": "I got caught up scrolling through Instagram.",
            "invalid_reason": "I’ll do it whenever I feel like it. It’s still done."
        },
        "very_late": {
            "valid_reason": "A blackout interrupted my entire evening schedule.",
            "weak_reason": "I just couldn't find the motivation earlier.",
            "invalid_reason": "Time is relative, isn’t it?"
        },
        "early": {
            "valid_reason": "I had a meeting scheduled during the task time, so I did it beforehand.",
            "weak_reason": "Wanted to free up my afternoon for gaming.",
            "invalid_reason": "Who cares when it's done, I’m efficient."
        }
    },

    "Write Reflection Journal": {
        "on_time": {
            "valid_reason": "Completed during my usual evening journaling hour.",
            "weak_reason": "Decided not to procrastinate this time.",
            "invalid_reason": "Why are we even tracking this?"
        },
        "late": {
            "valid_reason": "Had a long therapy session that overlapped with task time.",
            "weak_reason": "Started watching Netflix and forgot.",
            "invalid_reason": "I'll do it late if I want. Still counts."
        },
        "very_late": {
            "valid_reason": "Unexpected shift change at work threw off my schedule.",
            "weak_reason": "It didn’t feel urgent so I delayed it.",
            "invalid_reason": "I do what I want, deadlines are fake."
        },
        "early": {
            "valid_reason": "I anticipated I'd be tired later and planned ahead.",
            "weak_reason": "Wanted to rush through the day’s tasks.",
            "invalid_reason": "Because I felt like it. Duh."
        }
    },

    "Study Electromagnetic Induction": {
        "on_time": {
            "valid_reason": "Started studying immediately after class as planned.",
            "weak_reason": "Teacher reminded us today, so I figured why not.",
            "invalid_reason": "It’s school. We all suffer."
        },
        "late": {
            "valid_reason": "Got stuck helping a friend debug their project.",
            "weak_reason": "Distracted with mobile games.",
            "invalid_reason": "Chill, I’m not a robot."
        },
        "very_late": {
            "valid_reason": "Had to visit a hospital due to a family emergency.",
            "weak_reason": "I just didn’t feel like doing physics.",
            "invalid_reason": "I’m not here for gold stars."
        },
        "early": {
            "valid_reason": "I expected to be busy later with club activities.",
            "weak_reason": "Wanted to get it over with.",
            "invalid_reason": "Being early should be enough reason."
        }
    }
}


scheduled_duration = 90  # in minutes
task_difficulty = 1.5
# Start time fixed for all
base_start_time = datetime.strptime("09:00", "%H:%M")

# Timings by category
timing_profiles = {
    "on_time": {
        "start_time": base_start_time,
        "end_time": base_start_time + timedelta(minutes=90)
    },
    "late": {
        "start_time": base_start_time,
        "end_time": base_start_time + timedelta(minutes=135)  # 45 minutes late
    },
    "very_late": {
        "start_time": base_start_time,
        "end_time": base_start_time + timedelta(minutes=210)  # 2 hours late
    },
    "early": {
        "start_time": base_start_time,
        "end_time": base_start_time - timedelta(minutes=60)  # 1 hour early
    }
}

results = {}
models = {
    "llama3-70b-8192": assistant.config.get("default_model"),
    "qwen-qwq-32b": assistant.config.get("qwen"),
    "deepseek-r1-distill-llama-70b": assistant.config.get("deep_seek"),
    "gemma2-9b-it": assistant.config.get("google")
}

def run_test(*args):
    
    try:
        g = assistant.calculate_late_penalty_score(
            start_time=args[0],
            completion_time=args[1],
            scheduled_duration=args[2],
            reason=args[3],
            task_difficulty=args[4],
            task_description=args[5],
            model=args[6],
            test=args[7] 
        )

        return g
    except BadRequestError as e:
        print(f"Error : | {str(e)}")
        return None 

exec = ThreadPoolExecutor(max_workers=15)
temp_file = Path().cwd() /'temp.json'

for model_name, model_id in models.items():
    print(f"\n🚀 Starting tests for model: {model_name}")
    results[model_name] = {}

    for activity, timing_cases in tqdm(test_matrix.items()):
        activities_data = []

        for timing_label, reasons in timing_cases.items():
            timing = timing_profiles[timing_label]
            start_time = format_time(timing["start_time"])
            completion_time = format_time(timing["end_time"])
            
            reason_data = []

            def test(reason_type,reason_text):
               
                args = (start_time,completion_time,scheduled_duration,reason_text,task_difficulty,activity,model_id,False)
                g = run_test(*args)

                score ,model_reasoning = None ,None
                if isinstance(g,LlmPenalty):
                    score = g.score
                    model_reasoning = g.response
                results[model_name].setdefault(activity, {})

                data = { "score": score, "model_reason":model_reasoning,
                        "reason": reason_text,"reason_type":reason_type ,"timing_label":timing_label}
                
                return data
            
            futures = [exec.submit(test,reason_type,reason_text)for reason_type, reason_text in reasons.items()]
            for result in as_completed(futures):
                reason_data.append(result.result())

            
            activities_data.extend(reason_data)
            sleep(10)
        with open(temp_file,'w') as f:
            json.dump(results,f,indent=2)
       
        results[model_name][activity]=activities_data

        
    # Save intermediate result per model for resumability
    with open(f"penalty_results_{model_name}.json", "w") as f:
        json.dump(results[model_name], f, indent=2)

    print(f"✅ Finished tests for model: {model_name}")

# Optionally combine all into one file
with open("penalty_results_all_models.json", "w") as f:
    json.dump(results, f, indent=2)
