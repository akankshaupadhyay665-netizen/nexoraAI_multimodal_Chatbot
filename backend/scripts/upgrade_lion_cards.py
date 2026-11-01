import asyncio
import sys
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import sqlite3
from backend.services.image_gen_service import image_gen_service

async def main():
    db_path = BASE_DIR / "nexora.db"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    
    # Target the records shown in the user's screenshot
    records = cur.execute("""
        SELECT id, prompt, style, aspect_ratio, filename, file_path 
        FROM generated_media 
        WHERE prompt LIKE '%lion%' AND provider != 'Flux.1 Generative Studio' AND media_type = 'image'
    """).fetchall()
    
    print(f"Upgrading {len(records)} lion records...")
    for rec_id, prompt, style, aspect_ratio, filename, file_path in records:
        print(f"Generating for {rec_id} ({style} {aspect_ratio})...")
        res = await image_gen_service.generate_image(
            prompt="lion",
            style=style,
            aspect_ratio=aspect_ratio
        )
        print(f"Generated new file: {res['file_path']} (Provider: {res['provider']})")
        # Overwrite the old file path with the new image file content
        target_path = BASE_DIR / file_path if not Path(file_path).is_absolute() else Path(file_path)
        shutil.copyfile(res["file_path"], str(target_path))
        cur.execute("""
            UPDATE generated_media 
            SET provider = ? 
            WHERE id = ?
        """, (res["provider"], rec_id))
        con.commit()
        print(f"Updated record {rec_id} and overwritten {target_path.name} with real lion!")

    con.close()
    print("Done upgrading all lion images!")

if __name__ == "__main__":
    asyncio.run(main())
