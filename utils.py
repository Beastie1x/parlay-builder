import math
def american_to_prob(odds: int) -> float:
    return 100/(odds+100) if odds>0 else (-odds)/((-odds)+100)
