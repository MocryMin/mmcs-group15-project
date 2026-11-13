"""Source inventory and a portable analysis package; no remote publication."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parent
E=ROOT/'evidence'
URLS={
 'Lazard-LCOEplus-202506-archived20251025.pdf':
 'https://web.archive.org/web/20251025104311id_/https://www.lazard.com/media/5tlbhyla/lazards-lcoeplus-june-2025-_vf.pdf',
 'Tesla-Megapack-Maintenance-Agreement.pdf':
 'https://digitalassets.tesla.com/image/upload/prod/fulfillment/energy/Order/MegapackConfigurator/megapack-web-maintenance-agreement',
 'Tesla-Megapack-Equipment-Reservation.pdf':
 'https://digitalassets.tesla.com/image/upload/prod/fulfillment/energy/Order/MegapackConfigurator/megapack-web-purchase-equipment-only-agreement',
 'Tesla-Megapack-Installation-Reservation.pdf':
 'https://digitalassets.tesla.com/image/upload/prod/fulfillment/energy/Order/MegapackConfigurator/megapack-web-purchase-installation-agreement'
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    files=[]
    for name,url in URLS.items():
        p=E/name
        with pymupdf.open(p) as d:n=len(d)
        files.append(dict(file='evidence/'+name,url=url,pages=n,sha256=sha(p),bytes=p.stat().st_size,
                          retrieved='2026-11-10',access='anonymous Playwright MCP',
                          scope='public unsigned US contract template' if name.startswith('Tesla') else'Original publisher report recovered from public historical archive'))
    pages=[]
    for p in E.glob('pages-*.json'):
        data=json.loads(p.read_text(encoding='utf-8'))
        for rec in data:
            pages.append(dict(file='evidence/'+p.name,url=rec.get('url'),requested=rec.get('requested'),
                              status=rec.get('status'),error=rec.get('error'),sha256=sha(p)))
    sources=dict(as_of='2026-11-10',pdfs=files,pages=pages,
        NREL_source=dict(original='https://atb.nrel.gov/electricity/2024/utility-scale_battery_storage',
            archive='https://web.archive.org/web/20250919220637id_/https://atb.nrel.gov/electricity/2024/utility-scale_battery_storage',
            capture='evidence/pages-10-nrel.json',finding='15year maintained-capacity fixedOM2.5%CAPEX includes augmentation;no additionalVOM'),
        Tesla_specification=dict(previously_verified='../equipment-research-20261110-v3.1/evidence/Tesla-Megapack2XL-20230210.pdf',
            note='2023datasheet standard15yearequipment/retentionwarranty;raw2024/2026quotehas3.8544MWhvsrounded3.854'),
        interpretation_limits=['Quotes are five-unitCalifornia estimates,notactualpurchases orUKfirmprices',
            'Current directTesla andLazard endpoints blocked;publicarchives recovered facts without login',
            'Archive page JS disabled to prevent livecachebuster redirect;embedded publicSSR data read without ordering or livequote calls',
            'NRELcostfactor andLazardEPC/4hcosts transferred explicitly;notmanufacturerpromises',
            'LazardfirstyeargeneralOM is not totalwarranty/augmentationcost',
            'No hydrogentransport orstorage work in this round'],
        archive_scope='PortableZIP contains own analysis,numericalinputs,source pointers and selected data captures;full thirdpartyPDFs andLazardpageimages remain in local evidence,not redistributed inZIP')
    (ROOT/'SOURCES.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    broken=[]
    for p in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in target and not (p.parent/target.split('#')[0]).exists():broken.append((p.name,target))
    assert not broken,broken
    qa=json.loads((ROOT/'QA.json').read_text(encoding='utf-8'))
    qa.update(source_PDFs_hashed=len(files),local_links='pass',full_report_physical_pages=48,
              source_scope='Teslaquote6snapshots,maintenance2pages,installationselectedUI,Lazard19/42/43,NRELarchivedprimarypage')
    (ROOT/'QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    selected=list(ROOT.glob('*.md'))+[p for p in ROOT.glob('*.json') if p.name!='ANALYSIS_MANIFEST.json']+list(ROOT.glob('*.py'))
    selected += [E/name for name in ['pages-06-static-archive.json','pages-09-latest-quotes.json',
                                   'pages-10-nrel.json','2024-ui-selection.json']]
    manifest=dict(files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(selected)])
    (ROOT/'ANALYSIS_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    selected.append(ROOT/'ANALYSIS_MANIFEST.json')
    archive=ROOT.parent/'MMCS_Tesla_Lazard_Economics_20261110_v1.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in selected:z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rec in manifest['files']:
            assert hashlib.sha256(z.read(ROOT.name+'/'+rec['path'])).hexdigest()==rec['sha256']
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
         files=len(selected),rawPDFs_retained_locally=len(files),integrity='pass'),ensure_ascii=False))

if __name__=='__main__':run()
