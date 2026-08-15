import re

# Routing decisions (shipment-question / identity-info / human-request
# detection) moved to llm/intent_classifier.py's semantic classifier — see
# PROGRESS.md's Week 2 backlog note. The regex heuristics that used to live
# here kept missing real phrasings (a typo dodging the shipment keyword
# list, "talk with a human" dodging a "talk to"-only pattern), which is
# exactly the failure mode a classifier judging meaning instead of surface
# form doesn't have.
#
# TRACKING_CODE_PATTERN stays here and stays a regex: it isn't a routing
# decision, it's used by gating.py's _looks_like_shipment_disclosure as the
# actual enforcement backstop that scans an unverified reply for a leaked
# tracking number — that backstop needs to be deterministic, not another
# model call that could itself miss.
TRACKING_CODE_PATTERN = re.compile(r"\b[A-Za-z]{1,4}\d{6,}\b")
