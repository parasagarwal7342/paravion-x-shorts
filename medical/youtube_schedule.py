"""Schedule finished Shorts on YouTube (YouTube Data API v3).

Each episode is uploaded as PRIVATE with status.publishAt set, so YouTube publishes it automatically at that time.

Safety gates — an episode is skipped unless ALL are true:
  * final_video.mp4 and upload.json exist
  * timings.json engine == "elevenlabs"   (no preview-voice videos go out)
  * the episode folder contains APPROVED  (a human re-checked facts just before posting: `touch episodes/<slug>/APPROVED`)
  * publish_at is in the future

Setup (once):
  1. Google Cloud console → enable "YouTube Data API v3" → OAuth client ID (Desktop) → save as client_secret.json here.
  2. pip install google-api-python-client google-auth-oauthlib
  3. python3 youtube_schedule.py --upload     (first run opens a Google sign-in link; token saved to yt_token.json)

Default (no --upload) is a dry run that prints the plan.
Notes: YouTube's API cannot pin comments; the pinned-comment text is posted and must be pinned in YouTube Studio.
Custom thumbnails are not supported for Shorts; choose the frame in the YouTube app if needed.
"""
import argparse, datetime as dt, json, sys
from pathlib import Path

ROOT = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]


def episodes():
    for ep in sorted((ROOT / "episodes").iterdir()):
        u = ep / "upload.json"
        if not u.exists():
            continue
        meta = json.loads(u.read_text())
        tim = json.loads((ep / "timings.json").read_text()) if (ep / "timings.json").exists() else {}
        problems = []
        if not (ep / "final_video.mp4").exists(): problems.append("no video")
        if tim.get("engine") != "elevenlabs": problems.append("preview voice (needs ElevenLabs)")
        from medcheck import check as medcheck
        if medcheck(ep)[0]: problems.append("medcheck.py FAILED (run it for details)")
        if not (ep / "APPROVED").exists(): problems.append("not APPROVED (re-check facts, then touch APPROVED)")
        when = meta.get("publish_at")
        if not when: problems.append("no publish time")
        elif dt.datetime.fromisoformat(when) <= dt.datetime.now(dt.timezone.utc): problems.append("publish time passed")
        yield ep, meta, problems


def service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    tok = ROOT / "yt_token.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "client_secret.json"), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=False)
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(yt, ep, meta, synthetic):
    from googleapiclient.http import MediaFileUpload
    publish = dt.datetime.fromisoformat(meta["publish_at"]).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"], "categoryId": meta.get("category", "27")},
            "status": {"privacyStatus": "private", "publishAt": publish, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": synthetic}}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(ep / "final_video.mp4"), chunksize=-1, resumable=True))
    res = None
    while res is None:
        _, res = req.next_chunk()
    vid = res["id"]
    yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {
        "snippet": {"textOriginal": meta["pinned_comment"]}}}}).execute()
    (ep / "youtube.json").write_text(json.dumps({"video_id": vid, "publish_at": publish}, indent=1))
    return vid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true", help="actually upload (default: dry run)")
    ap.add_argument("--synthetic", action="store_true",
                    help="tick YouTube's 'altered or synthetic content' box (needed if realistic AI visuals are used)")
    a = ap.parse_args()
    yt = service() if a.upload else None
    for ep, meta, problems in episodes():
        done = (ep / "youtube.json").exists()
        status = "ALREADY SCHEDULED" if done else ("SKIP: " + "; ".join(problems) if problems else "READY")
        print(f"{meta.get('publish_at', '?'):27} {ep.name:32} {status}\n{'':27} “{meta['title']}”")
        if a.upload and not problems and not done:
            print("   uploaded, video id", upload(yt, ep, meta, a.synthetic))
