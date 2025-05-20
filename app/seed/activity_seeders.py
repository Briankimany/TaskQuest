
import json 
from app.utils.managers import ActivityManager
from app.config import TEST_USER_ID ,activites_seed_data
from app.init import create_app ,db
from app.utils.custom_errors import AppError ,RecordDuplicationError


def seed_activities(user_id):

    with create_app().app_context():
        try:
            manager = ActivityManager(user_id)
            
            with open(activites_seed_data) as f:
                data = json.load(f)
            
            for activity_data in data['activities']:
                print(activity_data['name'])
                try:

                    activity = manager.create_activity(activity_data['name'])
                except RecordDuplicationError as e:
                    print(e)
                    activity = manager.get_activity(activity_data['name'])
                
                skip_validation = data.get('skip_validation',False)
                
                for sub_data in activity_data['sub_activities']:
                    sub_data['activity_id'] = activity['id']
                    try:
                        manager.create_subactivity(
                            activity_id=activity['id'],
                            subactivity_data=sub_data,
                            skip_validation=skip_validation
                        )
                    except RecordDuplicationError:
                        continue

        except AppError as e:
            print(e)
            db.session.rollback()

if __name__ == "__main__":
    seed_activities(TEST_USER_ID)