"""Long-form with a custom pause between scenes: python3 longform_pad.py <work_dir> <seconds>"""
import sys
import longform as L
if __name__ == "__main__":
    L.PAD_AFTER = float(sys.argv[2])
    L.main(sys.argv[1])
