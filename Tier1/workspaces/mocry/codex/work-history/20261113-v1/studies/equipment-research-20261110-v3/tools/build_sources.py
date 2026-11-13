"""Index retained public primary sources and link product records to evidence."""
import hashlib
import json
import shutil
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'
URLS={
'TESVOLT-TALLON.pdf':'https://www.tesvolt.com/_media/02%20PRODUKTE/11_Tallon/TESVOLT_TALLON-Technisches_Datenblatt-DE.pdf',
'TESVOLT-POWERCORE-G2.pdf':'https://www.tesvolt.com/_media/02%20PRODUKTE/12_Forton_XL_PCG2/PC-G2_datasheet_Tesvolt.pdf',
'Sungrow-PowerStack255CS.pdf':'https://info-support.sungrowpower.com/datasheet-materials/b4f56963-dbd2-4c43-8cbc-0808eb4cf083.pdf',
'Sungrow-PowerStack255CS-manual.pdf':'https://info-support.sungrowpower.com/cms/af994f1d-bb0d-408a-b310-6ad732402c99/GUID-1A91AA58-F2F1-4A1B-B140-16A847F051DC_1_en-US_PDF%20(%E4%BA%A7%E5%93%81%E4%BF%A1%E6%81%AF%E8%AE%BE%E8%AE%A1%E9%83%A8_%E5%9F%BA%E7%A1%80%E7%89%88)_1786527819068_compressed.pdf',
'Sungrow-PowerTitan2-2H4H-V3.pdf':'https://info-support.sungrowpower.com/application/pdf/2024/02/21/DS_20230925_ST5015kWh-2500kW-2h_1250kW-4h_V3_EN.pdf',
'Sungrow-SC5000UD-MV-P3.pdf':'https://info-support.sungrowpower.com/datasheet-materials/141a8fd9-bd55-45eb-bed1-02ca586002d4.pdf',
'CATL-ESS-202406.pdf':'https://www.catl.com/en/uploads/1/file/public/202406/20240624152558_qft6x51t14.pdf',
'Huawei-LUNA241-2S1.pdf':'https://solar.huawei.com/dam/asset/view/91e4c6e06feb4284a0d71f515288352f.pdf',
'Huawei-LUNA215-2S10.pdf':'https://solar.huawei.com/dam/asset/view/135e950d5f0c40ffa317c4cd20554e08.pdf',
'Huawei-LUNA5015-2S.pdf':'https://solar.huawei.com/dam/asset/view/e9bb9b1319904298949861cb2d7c94ac.pdf',
'Huawei-PCS213KTL-H0.pdf':'https://solar.huawei.com/dam/asset/view/129065513be14d9e93f68ff542d4f2c9.pdf',
'neptune-2.pdf':'https://itm-power-assets.s3.eu-west-2.amazonaws.com/Neptune_II_Spec_Sheet_2_15_e7016ca8f8.pdf',
'neptune-5.pdf':'https://itm-power-assets.s3.eu-west-2.amazonaws.com/Neptune_V_Spec_Sheet_2_8_a3f68d4e43.pdf',
'ITM-Poseidon20-2-7.pdf':'https://itm-power-assets.s3.eu-west-2.amazonaws.com/POSEIDON_DATA_SHEET_2_7_2e1f89da3f.pdf',
'alpha-50.pdf':'https://itm-power-assets.s3.eu-west-2.amazonaws.com/14299_ITM_Alpha_Spec_Sheet_1_7_5db44f3d20.pdf',
'Nel-MC-Series-RevJ.pdf':'https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2021/01/MC-Series_PD-0600-0136-Rev-J.pdf',
'Nel-MC-Modular-RevA.pdf':'https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2025/10/MC-Series-Modular-Plants-PD-0600-0145-Rev-A-1.pdf',
'Nel-A485-Rev03.pdf':'https://96e597bb58d206f85397.b-cdn.net/wp-content/uploads/2024/08/A-Series-Spec-Sheet%E2%80%93DOC001974_03.pdf',
'Enapter-Flex120-202606.pdf':'https://enapter.com/wp-content/uploads/2025/05/2026-06-15_Datasheet_AEM-Flex120.pdf',
'Enapter-Nexus500-202606.pdf':'https://enapter.com/wp-content/uploads/2025/05/Datasheet_AEM-Nexus-500_15.06.2026.pdf',
'Enapter-Nexus1000-202606.pdf':'https://enapter.com/wp-content/uploads/2021/06/Datasheet_AEM-Nexus-1000_15.06.2026-1.pdf',
'Enapter-Nexus2500-202606.pdf':'https://enapter.com/wp-content/uploads/2026/07/Datasheet_AEM-Nexus2500_15.06.2026.pdf',
'Enapter-Rheos20-202606.pdf':'https://enapter.com/wp-content/uploads/2026/07/2026-06-15_Datasheet_AEM-RHEOS20.pdf',
'Enapter-2022-pricing-assumptions.pdf':'https://enapter.com/wp-content/uploads/2022/01/List-of-Assumptions-Enapter-Hydrogen-Pricing.pdf',
'BEIS-Hydrogen-Costs2021.pdf':'https://assets.publishing.service.gov.uk/media/611b710e8fa8f53dc994e59d/Hydrogen_Production_Costs_2021.pdf',
'BEIS-Hydrogen-Costs2021-Annex.xlsx':'https://assets.publishing.service.gov.uk/media/611a706ed3bf7f63a7b29216/Hydrogen_Production_Cost_2021_Annex.xlsx',
'DEA-storage.xlsx':'https://ens.dk/media/6589/download',
'PNNL-cost-performance-2024.xlsx':'https://www.pnnl.gov/sites/default/files/media/file/ESGC_Cost_Performance_Database_v2024.xlsx',
'IRENA-Green-Hydrogen-Cost2020.pdf':'https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf',
}

def build():
    files=[]
    for name,url in URLS.items():
        p=E/name
        assert p.is_file(),name
        record=dict(file='evidence/'+name,url=url,bytes=p.stat().st_size,
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest(),retrieved_date='2026-11-10',
                    access='Playwright MCP; TESVOLT and ITM2/5/50 raw PDFs reused from earlier same-day research where applicable',
                    source_type='manufacturer' if not name.startswith(('BEIS','DEA','PNNL','IRENA')) else'government_or_public_research')
        if p.suffix=='.pdf':
            with pymupdf.open(p) as doc: record['pdf_pages']=len(doc)
        files.append(record)
    pages=[]
    for p in sorted(E.glob('pages-*.json')):
        for rec in json.loads(p.read_text(encoding='utf-8')):
            pages.append(dict(capture='evidence/'+p.name,url=rec.get('url'),requested=rec.get('requested'),
                              title=rec.get('title'),http_status=rec.get('status'),error=rec.get('error'),
                              access='anonymous Playwright MCP',retrieved_date='2026-11-10'))
    legacy=json.loads((E/'tesvolt-prior-browser-pages.json').read_text(encoding='utf-8'))
    for rec in legacy:
        pages.append(dict(capture='evidence/tesvolt-prior-browser-pages.json',url=rec['url'],
                          retrieved_at=rec.get('retrieved_at'),access='earlier same-day Playwright MCP capture'))
    out=dict(as_of='2026-11-10',files=files,pages=pages,
             coverage='Manufacturer public sheets/manuals/pages, public government cost workbooks, original commercial order releases. Search failures and access-denied pages are not evidence of absence.',
             search_limits='Bing often returned empty shells; DuckDuckGo returned a human challenge. No challenge was bypassed. Direct manufacturer sources supplied the numerical evidence.')
    (ROOT/'SOURCES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SOURCES',len(files),'raw documents;',sum('pdf_pages' in x for x in files),'PDFs;',len(pages),'web capture entries')

if __name__=='__main__': build()
