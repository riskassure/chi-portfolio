import re
import json
import sqlite3
import os

def generate_slug(canonical_name):
    """Converts CamelCase canonical names into lowercase-dashed web slugs."""
    if not canonical_name:
        return None
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', canonical_name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    return s2.lower().replace('_', '-').replace('--', '-')

def transform_latex_content(raw_content):
    """Processes a raw LaTeX string and extracts its semantic layers."""
    metadata = {
        "canonical_name": None,
        "slug": None,
        "title": None,
        "created": None,
        "owner": None,
        "defines": [],
        "synonyms": [],
        "related": [],
        "classifications": [],
        "escaped_words": []
    }
    
    if not raw_content:
        return {"status": "error", "message": "No content provided to parse."}

    # --- BLOCK PROCESSING: Extraction & Sanitization ---
    try:
        # 1. Isolate the Header Block safely
        header_match = re.search(r'\\documentclass.*\\endmetadata', raw_content, re.DOTALL)
        if not header_match:
            return {"status": "error", "message": "No PlanetMath metadata header block found."}
        
        header_block = header_match.group(0)
        
        # 2. Parse Single-Value Metadata Tags
        canon_match = re.search(r'\\pmcanonicalname\{([^}]+)\}', header_block)
        title_match = re.search(r'\\pmtitle\{([^}]+)\}', header_block)
        created_match = re.search(r'\\pmcreated\{([^}]+)\}', header_block)
        owner_match = re.search(r'\\pmowner\{([^,}\s]+)\}', header_block)
        
        if canon_match: 
            metadata["canonical_name"] = canon_match.group(1).strip()
            metadata["slug"] = generate_slug(metadata["canonical_name"])
            
        if title_match: metadata["title"] = title_match.group(1).strip()
        if created_match: metadata["created"] = created_match.group(1).strip()
        if owner_match: metadata["owner"] = owner_match.group(1).strip()
        
        # 3. Parse Multi-Value Metadata Arrays
        metadata["defines"] = [t.strip() for t in re.findall(r'\\pmdefines\{([^}]+)\}', header_block)]
        metadata["synonyms"] = [s.strip() for s in re.findall(r'\\pmsynonym\{([^}]+)\}', header_block)]
        metadata["related"] = [r.strip() for r in re.findall(r'\\pmrelated\{([^}]+)\}', header_block)]
        
        class_matches = re.findall(r'\\pmclassification\{([^}]+)\}\{([^}]+)\}', header_block)
        metadata["classifications"] = [{"scheme": c[0].strip(), "code": c[1].strip()} for c in class_matches]

        # 4. Extract and Sanitize Document Body
        body_content = raw_content.split(r'\endmetadata')[-1].strip()
        
        # Harvest and strip the \PMlinkescapeword entries from the text body
        metadata["escaped_words"] = [w.strip() for w in re.findall(r'\\PMlinkescapeword\{([^}]+)\}', body_content)]
        body_content = re.sub(r'\\PMlinkescapeword\{[^}]+\}\n?', '', body_content)
        
        # 5. Transform inline linkage macros to our custom web-template style
        body_content = re.sub(r'\\[pP][mM]link(?:name|word)\{([^}]+)\}\{([^}]+)\}', r'{{LINK:\1|\2}}', body_content)
        
        # 6. Smart Handling of Preamble vs Body
        # Strip out any redundant \begin{document} or \end{document} if they exist
        body_content = re.sub(r'\\begin\{document\}\n?', '', body_content)
        body_content = re.sub(r'\\end\{document\}\n?', '', body_content)
        
        # Find any \usepackage{...} lines buried in the body content
        embedded_packages = re.findall(r'\\usepackage\{[^}]+\}\n?', body_content)
        
        # Clean those package declarations out of the body content so they don't cause errors
        body_content = re.sub(r'\\usepackage\{[^}]+\}\n?', '', body_content)
        
        # Build a dynamic, clean preamble
        # Core packages we want, plus whatever custom packages the file originally requested
        core_packages = ["\\usepackage{amssymb, amsmath, amsfonts}"]
        for pkg in embedded_packages:
            pkg_clean = pkg.strip()
            if pkg_clean not in core_packages:
                core_packages.append(pkg_clean)
                
        clean_header = (
            "\\documentclass[12pt]{article}\n" +
            "\n".join(core_packages) + "\n" +
            "\\begin{document}\n\n"
        )
        
        # Combine everything, making sure to append \end{document} nicely at the absolute end
        final_clean_tex = clean_header + body_content + "\n\n\\end{document}\n"

        return {
            "status": "success",
            "metadata": metadata,
            "cleaned_tex": final_clean_tex
        }

    except Exception as e:
        return {"status": "error", "message": f"Structural parsing exception: {str(e)}"}


# --- DATABASE FETCH & EXECUTION RUN ---
if __name__ == "__main__":
    # Adjust this path if your portfolio.db lives somewhere else relative to backend root
    db_path = r"C:\Development\chi-portfolio\backend\portfolio.db"
    
    # Target file name from the database table column
    target_file = "08A02-OperationsOnRelations.tex"
    
    print(f"Connecting to database at: {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query your specific staging table assuming the column name holding the text content is 'tex_content'
        # (Change 'tex_content' or 'file_name' below if your table columns use slightly different naming)
        query = "SELECT raw_content FROM stg_math_import WHERE file_name LIKE ?"
        cursor.execute(query, (f"%{target_file}%",))
        row = cursor.fetchone()
        
        if row:
            raw_tex_string = row[0]
            print(f"✅ Found content in database for {target_file}. Starting Extraction...\n")
            
            # Pass the database text string directly to the transformation function
            result = transform_latex_content(raw_tex_string)
            
            if result["status"] == "success":
                print("==============================")
                print("✅ STAGING DATA STRUCTURE GENERATED")
                print("==============================")
                print(json.dumps(result["metadata"], indent=4))
                
                # --- NEW: Write the full cleaned output to a file for complete inspection ---
                output_test_path = r"C:\Development\chi-portfolio\backend\src\utils\math\test_output.tex"
                with open(output_test_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(result["cleaned_tex"])
                
                print("\n==============================")
                print(f"💾 FULL FILE WRITTEN SUCCESSFULLY")
                print("==============================")
                print(f"You can now open and review the entire file here:\n--> {output_test_path}")
            else:
                print(f"❌ Extraction Error: {result['message']}")
        else:
            print(f"❌ Error: No records found matching '{target_file}' in stg_math_import table.")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error encountered: {str(e)}")