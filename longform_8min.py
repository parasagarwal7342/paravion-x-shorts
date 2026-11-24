"""Long-form with 1.25 s pauses between scenes (used to land a video just past 8:00 for mid-roll ads)."""
import sys
import longform as L
L.PAD_AFTER = 1.25
if __name__ == "__main__":
    L.main(sys.argv[1])
