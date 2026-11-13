"""Preserve the user-provided transcript pair and index the VTT timing."""
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

COURSE = Path(__file__).resolve().parents[3]
DOWNLOADS = Path(r"C:\Users\Mocry\Downloads")
OUT = COURSE / "materials/project-launch-transcripts-20261028"
OUT.mkdir(exist_ok=True)
names = ["MATHO Methodology, M-transcript.txt", "MATHO Methodology, M-transcript.vtt"]
manifest = []
for name in names:
    source, target = DOWNLOADS / name, OUT / name
    raw = source.read_bytes()
    if target.exists():
        assert target.read_bytes() == raw, "Do not overwrite a different source snapshot"
    else:
        shutil.copy2(source, target)
    manifest.append(dict(name=name, original_path=str(source), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))

txt = (OUT / names[0]).read_text(encoding="utf-8-sig")
vtt = (OUT / names[1]).read_text(encoding="utf-8-sig")
cues = []
pending = None
for block in re.split(r"\n\s*\n", vtt):
    lines = block.splitlines()
    timing = next((i for i,line in enumerate(lines) if "-->" in line), None)
    if timing is not None:
        start, end = lines[timing].split(" --> ")
        spoken = " ".join(lines[timing+1:])
        match = re.search(r"<v ([^>]+)>", spoken)
        pending = dict(index=len(cues)+1, start=start, end=end,
                       speaker=match.group(1) if match else None,
                       text=html.unescape(re.sub(r"<[^>]+>", "", spoken)))
        cues.append(pending)
    elif pending is not None and block.startswith("NOTE CONF "):
        pending["word_confidence"] = json.loads(block[len("NOTE CONF "):])["raw"]

normalize = lambda text: re.sub(r"\s+", " ", re.sub(r"SPEAKER \d+", "", text)).strip()
assert normalize(txt) == normalize(" ".join(c["text"] for c in cues))
assert len(cues) == 1596
record = dict(source_id="USER-MMCS-PROJECT-LAUNCH-TRANSCRIPTS-20261028", files=manifest,
              cue_count=len(cues), first_timestamp=cues[0]["start"], last_timestamp=cues[-1]["end"],
              text_and_vtt_identical_after_speaker_whitespace_normalization=True,
              audio_or_video_obtained=False, transcript_checked_against_audio=False)
(OUT / "manifest.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT / "cues.json").write_text(json.dumps(cues,ensure_ascii=False,indent=2),encoding="utf-8")

paragraphs = []
current = []
def flush():
    if current:
        paragraphs.append("["+current[0]["start"]+" - "+current[-1]["end"]+"] "+str(current[0]["speaker"])+"\n"+" ".join(c["text"] for c in current))
        current.clear()
def seconds(stamp):
    h,m,s = stamp.split(":")
    return 3600*int(h)+60*int(m)+float(s)
for cue in cues:
    if current and (cue["speaker"] != current[-1]["speaker"] or seconds(cue["start"])-seconds(current[0]["start"])>55):
        flush()
    current.append(cue)
flush()
(OUT / "transcript-timed.txt").write_text("\n\n".join(paragraphs)+"\n",encoding="utf-8")
print(json.dumps(record,ensure_ascii=False,indent=2))
