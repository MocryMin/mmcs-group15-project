"""Render the specification pages used for visual table/footnote inspection."""
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
jobs={'TESVOLT-TALLON.pdf':[1],'TESVOLT-POWERCORE-G2.pdf':[2],
      'Sungrow-PowerStack255CS.pdf':[2],'Sungrow-PowerTitan2-2H4H-V3.pdf':[2],
      'Huawei-LUNA215-2S10.pdf':[1],'Huawei-LUNA241-2S1.pdf':[1],
      'CATL-ESS-202406.pdf':[16,17],'Nel-MC-Series-RevJ.pdf':[1],
      'Nel-MC-Modular-RevA.pdf':[1],'Nel-A485-Rev03.pdf':[1],
      'Enapter-Nexus2500-202606.pdf':[2],'Enapter-Flex120-202606.pdf':[2],
      'Enapter-Rheos20-202606.pdf':[2]}
out=ROOT/'evidence'/'visual';out.mkdir(exist_ok=True)
for file,pages in jobs.items():
    doc=pymupdf.open(ROOT/'evidence'/file)
    for page in pages:
        doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(out/(Path(file).stem+f'-p{page}.png'))
print('RENDERED',sum(len(x) for x in jobs.values()),'specification pages')
