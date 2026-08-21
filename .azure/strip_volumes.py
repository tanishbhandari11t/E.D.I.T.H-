from pathlib import Path
import re

p = Path(r"c:\Users\Arnav Singh\Documents\Codes\hermes-agent-main\.azure\ca-jimmy.yaml")
text = p.read_text(encoding="utf-8")
text2 = re.sub(r"(?m)^      volumeMounts:\n(?:      - .*\n(?:        .*\n)*)+", "", text)
text2 = re.sub(r"(?m)^    volumes:\n(?:    - .*\n(?:      .*\n)*)+", "", text2)
if text2 == text:
    raise SystemExit("YAML edit made no changes — abort")
p.write_text(text2, encoding="utf-8")
print("removed volume mounts")
for i, line in enumerate(text2.splitlines(), 1):
    if "volume" in line.lower() or "mountPath" in line or "storageType" in line:
        print(f"{i}:{line}")
