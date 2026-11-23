"""Cinematic 9:16 Short with the long-form look (real photos, push-ins, grade, captions).
python3 longform_vertical.py <work_dir>  (same work_dir layout as longform.py)"""
import sys
import longform as L
L.W, L.H = 1080, 1920
L.BAR = 0          # no letterbox on vertical
L.PAD_AFTER = 0.3
L.TXT = 1.4
L.TITLE_Y = 760
L.CAP_Y = 1300
if __name__ == "__main__":
    L.main(sys.argv[1])
