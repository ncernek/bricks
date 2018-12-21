class Outbounds:
    HOW_IT_WORKS = """Instructions: every day, enter your most important task. At the end of the day, if you complete your task, you get +10 points. If you stay consistent, you get bonuses that double your points. Does this make sense? (y/n)"""

    WHAT_TIMEZONE = """What's your timezone?
a) PT
b) MT
c) CT
d) ET
"""

    MAIN_MENU = """MAIN MENU
{get_username}: +{get_total_points}pts
What do you want to do?
a) choose a task
b) invite a friend
c) create a team
d) view leaderboard
e) PROFILE MENU
"""

    RETRY = "Your response is not valid, try again.\n"

    PROFILE_MENU = """PROFILE MENU
What do you want to do?
a) change timezone
b) change username
c) help
d) MAIN MENU"""


class Points:
    DEFAULT = 0
    TASK_COMPLETED = 10
    CHOOSE_TASK = 1
    DID_YOU_DO_IT = 1
    EARNED_MESSAGE = "+{points} pt earned!"
    ALREADY_EARNED_MESSAGE = "+0 pt (already earned for today)."


class Statuses:
    PENDING = 'pending'
    ACTIVE = 'active'
    REJECTED = 'rejected'
    CONFIRMED = 'confirmed'


US_TIMEZONES = {
    'a': 'America/Los_Angeles',
    'b': 'America/Denver',
    'c': 'America/Chicago',
    'd': 'America/New_York',
}


class Redirects:
    MAIN_MENU = 'main_menu'