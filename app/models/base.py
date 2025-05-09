
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


# Constants
BASE_EXP = 100  # Default base experience points
STANDARD_TIME_UNIT = 60  # 1 hour in minutes
GRACE_PERIOD = 15  # 15-minute grace period for full EXP