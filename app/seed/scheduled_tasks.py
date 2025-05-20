
import json
from datetime import datetime, time
from typing import List, Dict
from app.config import TEST_USER_ID
from app.models import Activity, SubActivity
from app.utils.schedulers import TaskScheduler
from app.models import db
from app.config import seed_data_folder 
from app.init import create_app

def load_and_schedule_sessions(json_file_path: str):
    """
    Load JSON schedule and schedule all tasks using TaskScheduler
    
    Args:
        json_file_path: Path to JSON schedule file
    """

    with open(json_file_path) as f:
        scheduled_tasks = json.load(f)
    
    
    subactivity_map = create_subactivity_map()
    

    results = []
    for task in scheduled_tasks:

        activity_name, sub_name = task['subactivity_name'].split('.')
        subactivity_id = subactivity_map.get(f"{activity_name}.{sub_name}")
        
        if not subactivity_id:
            print(f"Subactivity not found: {task['subactivity_name']}")
            continue
        
        start_time = time.fromisoformat(task['start_time'])
        
        scheduler = TaskScheduler(
            user_id=TEST_USER_ID,
            date=datetime.strptime(task['date'], "%Y-%m-%d")
        )
        
        try:
            result = scheduler.schedule_with_buffer(
                sub_activity_id=subactivity_id,
                start_time=start_time,
                task_duration_hours=task['task_duration_hours'],
                buffer_duration=task['buffer_duration'],
                specific_buffer_name=task['specific_buffer_name'],
                buffer_name=task['buffer_name'],
                cyclic=task['cyclic']
            )
            results.append({
                'status': 'success',
                'task': task['subactivity_name'],
                'date': task['date'],
                'time': task['start_time'],
                'result': result
            })
        except Exception as e:
            results.append({
                'status': 'error',
                'task': task['subactivity_name'],
                'date': task['date'],
                'time': task['start_time'],
                'error': str(e)
            })
    
    return results

def create_subactivity_map() -> Dict[str, int]:
    """Create mapping of 'Activity.SubActivity' names to their IDs"""
    subactivities = SubActivity.query.join(Activity).filter(
        SubActivity.user_id == TEST_USER_ID
    ).all()
    
    return {
        f"{sub.activity.name}.{sub.name}": sub.id
        for sub in subactivities
    }

if __name__ == "__main__":

    schedule_file = seed_data_folder/"scheduled_tasks.json"
    
    print("Starting schedule import...")
    with create_app().app_context():
        results = load_and_schedule_sessions(schedule_file)
    

    successes = sum(1 for r in results if r['status'] == 'success')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\nImport complete: {successes} successful, {errors} failed")
    
    if errors > 0:
        print("\nFailed tasks:")
        for error in [r for r in results if r['status'] == 'error']:
            print(f"- {error['task']} on {error['date']} at {error['time']}: {error['error']}")