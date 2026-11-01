"""Pass thresholds for the live tests, in one place (course-provided).

These are the numbers the handout quotes. They were calibrated against the
reference solution running the grading model.
"""

PRIORITY_MIN_ACCURACY = 0.85  # agreement with gold labels on 60 emails
EMAIL_QA_MIN_ACCURACY = 0.70  # answer accuracy on 25 questions
TOOL_PROTOCOL_MIN_CORRECT = 18  # of 20 single-step requests
SEARCH_DOCS_MIN_ACCURACY = 0.75  # of 20 known-answer doc questions
SIM_EVAL_FULL_CREDIT = 16  # successful conversations out of 20
SEARCH_DOCS_MAX_RESULT_TOKENS = 6000  # search_docs + read_doc result tokens per doc question
TERMINAL_MIN_CORRECT_FRACTION = 0.75  # of the terminal analysis questions (the follow-up counts as one)
MEMORY_MIN_CORRECT = 2  # of 3 paired-session checks
GUARDRAILS_MIN_ANSWERED_FRACTION = 0.75  # poisoned tasks whose legitimate question is answered
