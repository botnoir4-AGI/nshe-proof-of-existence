
import requests

feeds = [
    ("CVE Details", "https://www.cvedetails.com/atom.php?cvssscoremin=7"),
    ("NVD Recent", "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=5"),
    ("MITRE CVE", "https://cve.circl.lu/cve/recent"),
]

for name, url in feeds:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "AUTARCH/1.0"})
        print(f"{name}: HTTP {r.status_code}, {len(r.text)} bytes")
        if r.status_code == 200:
            print(f"  Preview: {r.text[:150]}...")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
