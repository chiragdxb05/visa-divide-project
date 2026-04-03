"""
process_visa_data.py
--------------------
Data processing pipeline for "The Global Mobility Divide" visualisation.

Course:  GRAD-E1493 Data Journalism, Hertie School, Spring 2026
Author:  Chirag Ramesh (244897)

Source data:
  URL:  https://www.fiw.uni-bonn.de/de/forschung/demokratieforschung/team/dr-lena-laube/visa-network-data
  Mau, S., Gülzau, F., Laube, L., & Zaun, N. (2015).
  The Global Mobility Divide: How Visa Policies Have Evolved over Time.
  Journal of Ethnic and Migration Studies, 41(8).
  Appendix: Visa_Network_Data_1969_2010.xls

Hex coordinates:
  Generated via amCharts Pixel Map Generator (https://pixelmap.amcharts.com/)
  Settings: Equal Earth projection · World Ultra · 8px · Hexagon shape
  Output: worldUltra-pixel-map.html (included in repository)

This script:
  1. Reads visa-free destination counts from the Mau et al. XLS appendix
  2. Reads hex pixel coordinates from the amCharts export
  3. Merges both datasets by ISO3 country code
  4. Outputs a JSON file (visa_data.json) used by the interactive visualisation

Requirements:
  pip install xlrd pandas beautifulsoup4
"""

import json
import re
import xlrd
import pandas as pd
from bs4 import BeautifulSoup


# ── 1. READ VISA DATA FROM XLS ────────────────────────────────────────────────

def read_visa_data(xls_path):
    """
    Read visa-free destination counts from Mau et al. (2015) appendix XLS.
    Returns a dict: {ISO3: {"name": str, "a": int|None, "b": int|None}}
      where "a" = 1969 count, "b" = 2010 count
    """
    wb = xlrd.open_workbook(xls_path)

    # The appendix contains two sheets: one for 1969, one for 2010
    # Sheet structure: column 0 = country name, col 1 = ISO3, col 2 = visa-free count
    data = {}

    for sheet_name in wb.sheet_names():
        sh = wb.sheet_by_name(sheet_name)
        year_key = None

        if '1969' in sheet_name:
            year_key = 'a'
        elif '2010' in sheet_name:
            year_key = 'b'
        else:
            continue

        for row_idx in range(1, sh.nrows):  # skip header row
            country_name = str(sh.cell_value(row_idx, 0)).strip()
            iso3         = str(sh.cell_value(row_idx, 1)).strip().upper()
            count_raw    = sh.cell_value(row_idx, 2)

            if not iso3 or len(iso3) != 3:
                continue

            count = int(count_raw) if count_raw != '' else None

            if iso3 not in data:
                data[iso3] = {"name": country_name, "a": None, "b": None}

            data[iso3][year_key] = count

    print(f"  Loaded {len(data)} countries from XLS")
    return data


# ── 2. READ HEX COORDINATES FROM AMCHARTS EXPORT ─────────────────────────────

def read_hex_coords(html_path):
    """
    Parse hex pixel coordinates from amCharts Pixel Map Generator export.

    The amCharts export is an HTML file containing a JavaScript object with
    country data. Each country has an ISO2 code and an array of [x, y] pixel
    coordinates for its hex cells, in Equal Earth projected space
    (x ≈ [-1.9, 2.6], y ≈ [-0.95, 1.3]).

    Returns a dict: {ISO2: [[px, py], ...]}
    """
    with open(html_path, encoding='utf-8') as f:
        content = f.read()

    # Extract the countries JavaScript object from the amCharts HTML
    # It looks like: AM5.registry.entitiesById["..."].dataItems
    # We look for the pattern that lists areas with their pixel coords
    pattern = re.compile(
        r'"([A-Z]{2})"\s*:\s*\{[^}]*"pixelX"\s*:\s*([\-\d.]+)[^}]*"pixelY"\s*:\s*([\-\d.]+)',
        re.DOTALL
    )

    coords = {}
    for m in pattern.finditer(content):
        iso2 = m.group(1)
        px   = float(m.group(2))
        py   = float(m.group(3))
        if iso2 not in coords:
            coords[iso2] = []
        coords[iso2].append([round(px, 4), round(py, 4)])

    print(f"  Loaded hex coordinates for {len(coords)} countries from amCharts export")
    return coords


# ── 3. ISO2 → ISO3 MAPPING ────────────────────────────────────────────────────

# Manual mapping for the countries in this dataset
# (standard ISO 3166-1 alpha-2 to alpha-3)
ISO2_TO_ISO3 = {
    "AD": "AND", "AE": "ARE", "AF": "AFG", "AG": "ATG", "AL": "ALB",
    "AM": "ARM", "AO": "AGO", "AR": "ARG", "AT": "AUT", "AU": "AUS",
    "AZ": "AZE", "BA": "BIH", "BB": "BRB", "BD": "BGD", "BE": "BEL",
    "BF": "BFA", "BG": "BGR", "BH": "BHR", "BI": "BDI", "BJ": "BEN",
    "BN": "BRN", "BO": "BOL", "BR": "BRA", "BS": "BHS", "BT": "BTN",
    "BW": "BWA", "BY": "BLR", "BZ": "BLZ", "CA": "CAN", "CD": "COD",
    "CF": "CAF", "CG": "COG", "CH": "CHE", "CI": "CIV", "CL": "CHL",
    "CM": "CMR", "CN": "CHN", "CO": "COL", "CR": "CRI", "CU": "CUB",
    "CV": "CPV", "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DJ": "DJI",
    "DK": "DNK", "DO": "DOM", "DZ": "DZA", "EC": "ECU", "EE": "EST",
    "EG": "EGY", "ER": "ERI", "ES": "ESP", "ET": "ETH", "FI": "FIN",
    "FJ": "FJI", "FR": "FRA", "GA": "GAB", "GB": "GBR", "GE": "GEO",
    "GH": "GHA", "GM": "GMB", "GN": "GIN", "GQ": "GNQ", "GR": "GRC",
    "GT": "GTM", "GW": "GNB", "GY": "GUY", "HK": "HKG", "HN": "HND",
    "HR": "HRV", "HT": "HTI", "HU": "HUN", "ID": "IDN", "IE": "IRL",
    "IL": "ISR", "IN": "IND", "IQ": "IRQ", "IR": "IRN", "IS": "ISL",
    "IT": "ITA", "JM": "JAM", "JO": "JOR", "JP": "JPN", "KE": "KEN",
    "KG": "KGZ", "KH": "KHM", "KM": "COM", "KP": "PRK", "KR": "KOR",
    "KW": "KWT", "KZ": "KAZ", "LA": "LAO", "LB": "LBN", "LR": "LBR",
    "LS": "LSO", "LT": "LTU", "LU": "LUX", "LV": "LVA", "LY": "LBY",
    "MA": "MAR", "MD": "MDA", "ME": "MNE", "MG": "MDG", "MK": "MKD",
    "ML": "MLI", "MM": "MMR", "MN": "MNG", "MR": "MRT", "MT": "MLT",
    "MU": "MUS", "MW": "MWI", "MX": "MEX", "MY": "MYS", "MZ": "MOZ",
    "NA": "NAM", "NE": "NER", "NG": "NGA", "NI": "NIC", "NL": "NLD",
    "NO": "NOR", "NP": "NPL", "NZ": "NZL", "OM": "OMN", "PA": "PAN",
    "PE": "PER", "PG": "PNG", "PH": "PHL", "PK": "PAK", "PL": "POL",
    "PT": "PRT", "PW": "PLW", "PY": "PRY", "QA": "QAT", "RO": "ROU",
    "RS": "SRB", "RU": "RUS", "RW": "RWA", "SA": "SAU", "SB": "SLB",
    "SD": "SDN", "SE": "SWE", "SG": "SGP", "SI": "SVN", "SK": "SVK",
    "SL": "SLE", "SM": "SMR", "SN": "SEN", "SO": "SOM", "SR": "SUR",
    "SS": "SSD", "ST": "STP", "SV": "SLV", "SY": "SYR", "SZ": "SWZ",
    "TD": "TCD", "TG": "TGO", "TH": "THA", "TJ": "TJK", "TL": "TLS",
    "TM": "TKM", "TN": "TUN", "TO": "TON", "TR": "TUR", "TT": "TTO",
    "TW": "TWN", "TZ": "TZA", "UA": "UKR", "UG": "UGA", "US": "USA",
    "UY": "URY", "UZ": "UZB", "VE": "VEN", "VN": "VNM", "VU": "VUT",
    "WS": "WSM", "YE": "YEM", "ZA": "ZAF", "ZM": "ZMB", "ZW": "ZWE",
}


# ── 4. MERGE AND OUTPUT ───────────────────────────────────────────────────────

def merge_and_export(visa_data, hex_coords, output_path):
    """
    Merge visa data with hex coordinates and write to JSON.
    Only countries present in BOTH datasets are included.
    """
    merged = {}

    for iso2, pts in hex_coords.items():
        iso3 = ISO2_TO_ISO3.get(iso2)
        if not iso3:
            continue
        if iso3 not in visa_data:
            continue

        entry = visa_data[iso3]
        merged[iso3] = {
            "n":   entry["name"],
            "a":   entry["a"],     # visa-free destinations in 1969
            "b":   entry["b"],     # visa-free destinations in 2010
            "pts": pts             # Equal Earth hex coordinates [[px, py], ...]
        }

    print(f"  Merged dataset: {len(merged)} countries")

    with open(output_path, 'w') as f:
        json.dump(merged, f, separators=(',', ':'))

    print(f"  Written to {output_path}")
    return merged


# ── 5. SUMMARY STATISTICS ─────────────────────────────────────────────────────

def print_summary(merged):
    """Print key statistics matching those cited in the article."""
    both = {k: v for k, v in merged.items() if v['a'] is not None and v['b'] is not None}

    vals_a = [v['a'] for v in both.values()]
    vals_b = [v['b'] for v in both.values()]
    deltas = [v['b'] - v['a'] for v in both.values()]

    print("\n── Summary Statistics ──────────────────────────────────")
    print(f"  Countries with data for both years: {len(both)}")
    print(f"  Global avg visa-free destinations 1969: {sum(vals_a)/len(vals_a):.1f}")
    print(f"  Global avg visa-free destinations 2010: {sum(vals_b)/len(vals_b):.1f}")

    # OECD countries (approximate set used in Mau et al.)
    OECD = {'AUS','AUT','BEL','CAN','CHE','CZE','DEU','DNK','ESP','FIN',
            'FRA','GBR','GRC','HUN','IRL','ISL','ITA','JPN','KOR','LUX',
            'MEX','NLD','NOR','NZL','POL','PRT','SVK','SWE','TUR','USA'}
    oecd_a = [v['a'] for k,v in both.items() if k in OECD and v['a'] is not None]
    oecd_b = [v['b'] for k,v in both.items() if k in OECD and v['b'] is not None]
    print(f"  OECD avg 1969: {sum(oecd_a)/len(oecd_a):.1f}")
    print(f"  OECD avg 2010: {sum(oecd_b)/len(oecd_b):.1f}")
    print(f"  OECD avg change: +{sum(oecd_b)/len(oecd_b) - sum(oecd_a)/len(oecd_a):.1f}")

    # Top 5 gainers and losers
    sorted_delta = sorted(both.items(), key=lambda x: x[1]['b'] - x[1]['a'])
    print("\n  Top 5 losers (1969→2010):")
    for iso, v in sorted_delta[:5]:
        print(f"    {iso} ({v['n']}): {v['a']} → {v['b']}  (Δ {v['b']-v['a']})")
    print("  Top 5 gainers (1969→2010):")
    for iso, v in sorted_delta[-5:][::-1]:
        print(f"    {iso} ({v['n']}): {v['a']} → {v['b']}  (Δ +{v['b']-v['a']})")
    print("────────────────────────────────────────────────────────")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Step 1: Reading visa data from Mau et al. XLS appendix...")
    visa_data = read_visa_data("data/Visa_Network_Data_1969_2010.xls")

    print("\nStep 2: Reading hex coordinates from amCharts export...")
    hex_coords = read_hex_coords("data/worldUltra-pixel-map.html")

    print("\nStep 3: Merging datasets...")
    merged = merge_and_export(visa_data, hex_coords, "data/visa_data.json")

    print_summary(merged)

    print("\nDone. The file data/visa_data.json is used by article_short_vf.html.")
    print("Note: The visualisation embeds this data inline as a JS const D={} object.")
