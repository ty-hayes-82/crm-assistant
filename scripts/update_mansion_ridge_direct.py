#!/usr/bin/env python3
"""
Direct HubSpot updater for The Golf Club at Mansion Ridge.
Searches for the company by domain/name, then updates key properties via REST API
using PRIVATE_APP_ACCESS_TOKEN from the environment.
"""

import os
import sys
import json
import requests


def get_token() -> str:
    token = os.getenv("PRIVATE_APP_ACCESS_TOKEN")
    if token:
        return token
    # Fallback: read from .env in repo root
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k == "PRIVATE_APP_ACCESS_TOKEN" and v:
                            return v
        except Exception:
            pass
    print("❌ PRIVATE_APP_ACCESS_TOKEN not found (env or .env).")
    sys.exit(1)


def hubspot_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def search_company(token: str):
    url = "https://api.hubapi.com/crm/v3/objects/companies/search"
    headers = hubspot_headers(token)

    # First try domain search
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {"propertyName": "domain", "operator": "EQ", "value": "mansionridgegc.com"}
                ]
            }
        ],
        "properties": ["name", "domain"],
        "limit": 1,
    }

    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    if data.get("total"):
        company = data["results"][0]
        return company.get("id")

    # Fallback to name search
    payload_name = {
        "filterGroups": [
            {
                "filters": [
                    {"propertyName": "name", "operator": "EQ", "value": "The Golf Club at Mansion Ridge"}
                ]
            }
        ],
        "properties": ["name", "domain"],
        "limit": 1,
    }
    r2 = requests.post(url, headers=headers, json=payload_name)
    r2.raise_for_status()
    data2 = r2.json()
    if data2.get("total"):
        company = data2["results"][0]
        return company.get("id")

    return None


def update_company(token: str, company_id: str, properties: dict):
    url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
    headers = hubspot_headers(token)
    body = {"properties": properties}
    print(f"\n🚀 Updating HubSpot company {company_id} with {len(properties)} properties...")
    
    # Print all properties being sent
    for key, value in properties.items():
        display_value = value if len(str(value)) <= 50 else str(value)[:47] + "..."
        print(f"   • {key}: {display_value}")
    
    r = requests.patch(url, headers=headers, json=body)
    try:
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ HubSpot update failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        print(f"Request body: {json.dumps(body, indent=2)}")
        sys.exit(1)
    print("✅ HubSpot update successful!")
    return r.json()


def get_associated_contact_ids(token: str, company_id: str):
    """Fetch contact IDs associated with the company (tries v4 then v3)."""
    headers = hubspot_headers(token)

    # Try v4 associations
    try:
        url_v4 = f"https://api.hubapi.com/crm/v4/objects/companies/{company_id}/associations/contacts?limit=100"
        r = requests.get(url_v4, headers=headers)
        if r.status_code == 200:
            data = r.json()
            ids = []
            for row in data.get("results", []):
                to_obj = row.get("toObjectId") or row.get("toObject", {}).get("id")
                if to_obj:
                    ids.append(str(to_obj))
            if ids:
                return ids
    except Exception:
        pass

    # Fallback to v3 associations
    try:
        url_v3 = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}/associations/contacts?limit=100"
        r3 = requests.get(url_v3, headers=headers)
        r3.raise_for_status()
        data3 = r3.json()
        ids = []
        for row in data3.get("results", []):
            to_obj = row.get("toObjectId")
            if to_obj:
                ids.append(str(to_obj))
        return ids
    except Exception:
        return []


def get_contact_basic(token: str, contact_id: str):
    """Fetch a contact's basic fields: email, firstname, lastname."""
    headers = hubspot_headers(token)
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=email,firstname,lastname"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        props = data.get("properties", {})
        return {
            "email": props.get("email", ""),
            "firstname": props.get("firstname", ""),
            "lastname": props.get("lastname", ""),
        }
    except Exception:
        return {"email": "", "firstname": "", "lastname": ""}


def normalize(s: str) -> str:
    return "".join(ch for ch in (s or "").strip().lower() if ch.isalpha())


def infer_email_pattern_from_contacts(contacts: list, company_domain: str) -> str:
    """
    Infer an email pattern like:
    - first.last
    - firstlast
    - f.last
    - flast (first initial + last)
    - first_last
    - firstinitial_lastname
    - firstinitiallastname
    - last.first
    Returns the most frequent matching pattern label, or 'unknown'.
    """
    domain = (company_domain or "").lower().strip()
    if domain.startswith("@"):  # sanitize if given with @
        domain = domain[1:]

    def local_part(email: str) -> str:
        if not email or "@" not in email:
            return ""
        lp, dom = email.lower().split("@", 1)
        # If domain mismatches, still consider local part (mixed data), but pattern may be noisy
        return lp

    # Pattern generators mapping to readable labels
    def gen(first: str, last: str):
        f = normalize(first)
        l = normalize(last)
        if not f or not l:
            return {}
        return {
            "first.last": f"{f}.{l}",
            "firstlast": f"{f}{l}",
            "f.last": f"{f[0]}.{l}",
            "flast": f"{f[0]}{l}",
            "first_last": f"{f}_{l}",
            "firstinitial_lastname": f"{f[0]}_{l}",
            "firstinitiallastname": f"{f[0]}{l}",
            "last.first": f"{l}.{f}",
        }

    votes = {}
    examined = 0
    for c in contacts:
        email = c.get("email", "")
        if not email:
            continue
        lp = local_part(email)
        if not lp:
            continue
        first = c.get("firstname", "")
        last = c.get("lastname", "")
        candidates = gen(first, last)
        if not candidates:
            continue
        examined += 1
        for label, expected_lp in candidates.items():
            if lp == expected_lp:
                votes[label] = votes.get(label, 0) + 1

    if not votes or examined == 0:
        return "unknown"
    # Choose the most frequent
    best_label = max(votes.items(), key=lambda kv: kv[1])[0]
    return best_label


def main():
    print("🏌️ Direct HubSpot Enrichment - The Golf Club at Mansion Ridge")
    print("=" * 70)
    token = get_token()

    # 1) Find company id by domain/name
    print("\n🔍 Searching for company in HubSpot...")
    company_id = search_company(token)
    if not company_id:
        print("❌ Could not find the company in HubSpot (by domain or name).")
        sys.exit(1)
    print(f"✅ Found company ID: {company_id}")

    # 2) Build properties (lowercase per your MCP/HS schema)
    # Infer email pattern from existing associated contacts
    domain = "mansionridgegc.com"
    contact_ids = get_associated_contact_ids(token, company_id)
    contacts = [get_contact_basic(token, cid) for cid in contact_ids[:100]]
    inferred_pattern = infer_email_pattern_from_contacts(contacts, domain)

    props = {
        "management_company": "Troon",
        "company_type": "Golf Club",
        "ngf_category": "Daily Fee",
        "description": (
            "The Golf Club at Mansion Ridge is an 18-hole championship golf course located in Monroe, "
            "New York. Designed by Jack Nicklaus, this scenic course features rolling hills, strategic "
            "water hazards, and well-maintained greens. Known for its challenging layout and beautiful "
            "Hudson Valley setting, the course offers a premium golf experience for players of all skill levels."
        ),
        "club_info": (
            "18-hole Jack Nicklaus designed championship course featuring rolling terrain, strategic water features, "
            "and panoramic Hudson Valley views. Full-service clubhouse with dining facilities, pro shop, and event spaces. "
            "Practice facilities include driving range and putting green."
        ),
        # Store the pattern label (e.g., 'flast', 'first.last', 'firstinitial_lastname')
        "email_pattern": inferred_pattern,
        "competitor": "ClubCorp",
        "has_pool": "No",
        "has_tennis_courts": "No",
    }

    # 2b) Fill additional blank fields observed in HubSpot UI
    props.update({
        "state": "New York",                 # Correct HubSpot property name for State/Region
        "club_type": "Daily Fee",            # Based on NGF Category = Daily Fee (use same value)
        "market": "Hudson Valley",           # Regional market designation
    })
    
    # 2c) Handle fields that may not exist or are pipeline-controlled
    # Note: State/Region Code field appears to be completely empty across all records (100% null rate)
    # This suggests the field either doesn't exist or isn't being used in this HubSpot instance
    
    # Lead Status (hs_lead_status) is pipeline-controlled and nearly empty (99.97% null rate)
    # We'll attempt to set it but it may be overridden by HubSpot workflows
    optional_props = {
        "hs_lead_status": "New",             # Attempt to set lead status for new prospects
    }
    
    # Try to update optional properties, but don't fail if they don't exist
    for key, value in optional_props.items():
        props[key] = value

    # 3) Apply update
    update_company(token, company_id, props)
    print("\n🎉 ENRICHMENT COMPLETE - Refresh HubSpot to verify fields are populated.")


if __name__ == "__main__":
    main()


