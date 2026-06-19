# backend/src/utils/math/run_pipeline.py

import time
from math_classification_lookup import migrate_and_populate_classifications
from step0_ingest_and_harvest import run_ingest_and_harvest
from step1_load_relational import build_relational_tables

def main():
    print("====================================================")
    print("🎬 STARTING MASTER MATHEMATICAL DATA PIPELINE RUN")
    print("====================================================\n")
    start_time = time.time()
    
    # PHASE 1: Rebuild base math_classifications lookups safely BEFORE bridges exist
    print("📌 [PHASE 1] Migrating Master MSC Classifications from CSV...")
    migrate_and_populate_classifications()
    print("-" * 50)
    
    # PHASE 2: Gather dynamic file types and cache raw documents into staging tables
    print("📌 [PHASE 2] Harvesting Local Files & Seeding Base Document Types...")
    run_ingest_and_harvest()
    print("-" * 50)
    
    # PHASE 3: Relate components using strong cross-references and foreign keys
    print("📌 [PHASE 3] Compiling Relational Core Structures...")
    build_relational_tables()
    
    end_time = time.time()
    elapsed = end_time - start_time
    print("\n====================================================")
    print(f"🎉 PIPELINE EXECUTION SUCCESSFUL (Total Time: {elapsed:.2f}s)")
    print("====================================================")

if __name__ == "__main__":
    main()