"""Long-form with longer breathing pauses between scenes (used for ~10-minute videos)."""
import sys
import longform as L
L.PAD_AFTER = 1.0
if __name__ == "__main__":
    L.main(sys.argv[1])
