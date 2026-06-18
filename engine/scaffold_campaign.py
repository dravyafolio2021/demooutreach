#!/usr/bin/env python3
import os
import sys
import json
import argparse
import re
from datetime import datetime

def parse_budget_factor(budget_str):
    """
    Parses a budget string like '3K-8K', '5K-10K', '10K', '5000' and calculates
    a scaling factor relative to the base of 5.5K (which maps factor to 1.0).
    """
    if not budget_str:
        return 1.0

    # Clean the string
    clean_str = budget_str.upper().replace('$', '').replace(' ', '').replace('~', '')
    
    # Try to find ranges like '3K-8K'
    match = re.match(r'(\d+(?:\.\d+)?)[K]?-(\d+(?:\.\d+)?)[K]?', clean_str)
    if match:
        val1 = float(match.group(1))
        val2 = float(match.group(2))
        # If 'K' wasn't matched explicitly, check if numbers are small (e.g. 3-8 means 3K-8K)
        if 'K' not in clean_str:
            if val1 < 100 and val2 < 100:
                pass # Already in K unit
            else:
                val1 = val1 / 1000.0
                val2 = val2 / 1000.0
        avg = (val1 + val2) / 2.0
        # Scale relative to base average of 5.5K
        return avg / 5.5
    
    # Try to find a single number like '5K' or '5000'
    match_single = re.match(r'(\d+(?:\.\d+)?)[K]?', clean_str)
    if match_single:
        val = float(match_single.group(1))
        if 'K' not in clean_str and val >= 100:
            val = val / 1000.0
        # Scale relative to 5.5K
        return val / 5.5
        
    return 1.0

def sanitize_slug(name):
    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')

def main():
    parser = argparse.ArgumentParser(description="Scaffold an outreach landing page campaign.")
    parser.add_argument("--name", required=True, help="Name of the prospect (e.g., 'Shutterink')")
    parser.add_argument("--founders", required=True, help="Co-founders names (e.g., 'Nitin Dangwal & Sandeep Mohan')")
    parser.add_argument("--location", required=True, help="Location of the studio (e.g., 'Delhi')")
    parser.add_argument("--specialty", required=True, help="Specialty/Hook line (e.g., 'Photojournalistic pioneers. International recognition.')")
    parser.add_argument("--website", required=True, help="Prospect website url")
    parser.add_argument("--ig", required=True, help="Prospect IG handle or email (e.g. '@shutterink.in')")
    parser.add_argument("--budget", default="3K-8K", help="Prospect budget range (e.g. '3K-8K')")
    parser.add_argument("--limit", type=int, default=25, help="Strict commission limit (e.g. 25)")
    parser.add_argument("--crew", type=int, default=6, help="Crew size (e.g. 6)")
    parser.add_argument("--folder", help="Target folder name (optional slug)")
    parser.add_argument("--industry", default="photography", help="Industry subfolder (photography, dental, etc.)")
    parser.add_argument("--no-db", action="store_true", help="Skip updating db.json")

    args = parser.parse_args()

    project_root = "/Users/shravya/Desktop/Outreach"
    engine_dir = os.path.join(project_root, "engine")
    
    # Choose template based on industry/template argument
    industry_clean = args.industry.lower().strip().replace("-", "_")
    if industry_clean == "real_estate" or industry_clean == "realestate":
        template_name = "real_estate_template.html"
    elif industry_clean == "dental":
        template_name = "dental_template.html"
    elif industry_clean == "salon":
        template_name = "salon_template.html"
    else:
        template_name = "wedding_template.html"
        
    template_path = os.path.join(engine_dir, template_name)
    db_path = os.path.join(engine_dir, "db.json")

    # Generate folder name slug
    folder_slug = args.folder if args.folder else sanitize_slug(args.name)
    industry_dir = os.path.join(project_root, args.industry)
    os.makedirs(industry_dir, exist_ok=True)
    target_dir = os.path.join(industry_dir, folder_slug)
    assets_dir = os.path.join(target_dir, "assets")

    print(f"Scaffolding campaign for '{args.name}'...")
    print(f"Slug folder: {folder_slug}")
    print(f"Using template: {template_name}")

    # Create directories
    os.makedirs(assets_dir, exist_ok=True)
    print(f"Created assets directory: {assets_dir}")

    # Read template
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Calculate scaled prices
    F = parse_budget_factor(args.budget)
    print(f"Budget '{args.budget}' maps to scaling factor: {F:.2f}")

    # Photography prices
    intimate_min, intimate_max = 3.0 * F, 4.5 * F
    multiday_min, multiday_max = 5.5 * F, 8.0 * F
    dest1_min, dest1_max = 9.0 * F, 12.0 * F
    dest2_min, dest2_max = 10.0 * F, 15.0 * F
    doc_min, doc_max = 1.8 * F, 2.5 * F

    # Real Estate prices (in Crores)
    re_2bhk_min, re_2bhk_max = 1.5 * F, 2.5 * F
    re_3bhk_min, re_3bhk_max = 3.0 * F, 5.0 * F
    re_penthouse_min, re_penthouse_max = 7.0 * F, 12.0 * F

    # Format Rupee values nicely
    def fmt_lakh(val):
        return f"₹{val:.1f}L".replace(".0L", "L")

    def fmt_crore(val):
        return f"₹{val:.1f} Cr".replace(".0 Cr", " Cr")

    # Replacement values dictionary
    replacements = {
        "{{PROSPECT_NAME}}": args.name,
        "{{PROSPECT_NAME_UPPER}}": args.name.upper(),
        "{{PROSPECT_FOLDER}}": folder_slug,
        "{{FOUNDERS}}": args.founders,
        "{{LOCATION}}": args.location,
        "{{LOCATION_UPPER}}": args.location.upper(),
        "{{SPECIALTY}}": args.specialty,
        "{{WEBSITE}}": args.website,
        "{{EMAIL_OR_IG}}": args.ig,
        "{{COMMISSIONS_LIMIT}}": str(args.limit),
        "{{CREW_SIZE}}": str(args.crew),
        "{{INTIMATE_PRICE_RANGE}}": f"{fmt_lakh(intimate_min)} - {fmt_lakh(intimate_max)}",
        "{{MULTIDAY_PRICE_RANGE}}": f"{fmt_lakh(multiday_min)} - {fmt_lakh(multiday_max)}",
        "{{DESTINATION_PRICE_RANGE_1}}": f"{fmt_lakh(dest1_min)} - {fmt_lakh(dest1_max)}",
        "{{DESTINATION_PRICE_RANGE_2}}": f"{fmt_lakh(dest2_min)} - {fmt_lakh(dest2_max)}",
        "{{DOCUMENTARY_PRICE_RANGE}}": f"{fmt_lakh(doc_min)} - {fmt_lakh(doc_max)}",
        "{{RE_2BHK_PRICE_RANGE}}": f"{fmt_crore(re_2bhk_min)} - {fmt_crore(re_2bhk_max)}",
        "{{RE_3BHK_PRICE_RANGE}}": f"{fmt_crore(re_3bhk_min)} - {fmt_crore(re_3bhk_max)}",
        "{{RE_PENTHOUSE_PRICE_RANGE}}": f"{fmt_crore(re_penthouse_min)} - {fmt_crore(re_penthouse_max)}",
        "{{FILM_1_TITLE}}": "Dhruv & Pippa",
        "{{FILM_2_TITLE}}": "Palak & Priya",
        "{{FILM_3_TITLE}}": "Indu & Sahil",
        "{{FILM_4_TITLE}}": "Avi & Vai"
    }

    # Perform substitutions
    page_content = template_content
    for placeholder, val in replacements.items():
        page_content = page_content.replace(placeholder, val)

    # Write output file
    index_out = os.path.join(target_dir, "index.html")
    with open(index_out, "w", encoding="utf-8") as f:
        f.write(page_content)
    print(f"Generated index page: {index_out}")

    # Admin template processing
    admin_template_name = "real_estate_admin_template.html" if args.industry == "real-estate" else "admin_template.html"
    admin_template_path = os.path.join(engine_dir, admin_template_name)
    if os.path.exists(admin_template_path):
        with open(admin_template_path, "r", encoding="utf-8") as f:
            admin_content = f.read()
        
        for placeholder, val in replacements.items():
            admin_content = admin_content.replace(placeholder, val)
            
        admin_out = os.path.join(target_dir, "admin.html")
        with open(admin_out, "w", encoding="utf-8") as f:
            f.write(admin_content)
        print(f"Generated admin page: {admin_out}")

    # Fallback assets are now loaded from the central /defaults directory.
    # No need to copy them to individual directories.

    # Update db.json
    if not args.no_db:
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    db = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to parse db.json ({e}). Creating new structure.")
                db = {"emails": [], "agents": [], "workspaces": [], "prospects": []}
        else:
            db = {"emails": [], "agents": [], "workspaces": [], "prospects": []}

        # Find default workspace ID
        workspace_id = "workspace_1780145932542" # Default fallback
        if db.get("workspaces"):
            workspace_id = db["workspaces"][0]["id"]

        # Check if prospect already exists
        prospect_email = args.ig # using handle/email as unique key
        existing_prospect = None
        for p in db.get("prospects", []):
            if p.get("email") == prospect_email:
                existing_prospect = p
                break

        if existing_prospect:
            print(f"Updating existing database record for {args.name}")
            existing_prospect["name"] = args.name
            existing_prospect["assignedAt"] = datetime.utcnow().isoformat() + "Z"
        else:
            print(f"Adding new database record for {args.name}")
            new_prospect = {
                "email": prospect_email,
                "name": args.name,
                "workspaceId": workspace_id,
                "assignedAt": datetime.utcnow().isoformat() + "Z"
            }
            db.setdefault("prospects", []).append(new_prospect)

        # Write back db.json
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
        print("Updated db.json successfully.")
    else:
        print("Skipped db.json update as requested.")
    print("Scaffolding complete!")

if __name__ == "__main__":
    main()
