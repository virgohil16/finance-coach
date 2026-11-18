"""Settings for finance-coach. Change these to match your own job/visa."""
from datetime import date

# Hungry Jack's pay
BASE_RATE = 39.68      # ordinary hourly rate (fallback)
NIGHT_RATE = 52.00     # overnight rate - all my shifts are overnight
PAY_DAY = "Wednesday"  # paid weekly

# Student visa condition 8105
VISA_HOUR_LIMIT = 48   # max hours in any 2-week window while course is in session
WARNING_BUFFER = 4     # start warning when within this many hours of the limit

# Course breaks - unlimited hours allowed here
# PLACEHOLDER: replace with real dates from the Monash academic calendar
COURSE_BREAKS = [
    (date(2026, 6, 20), date(2026, 7, 26)),
]

# LLM settings - check console.groq.com/docs/models if this stops working
LLM_MODEL = "openai/gpt-oss-20b"