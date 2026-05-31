




"""
Run this once locally: python setup_structure.py
It moves flat files into the correct package subfolders,
then you commit and push the whole thing to GitHub.
"""
import os, shutil

def move(src, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)
    init = os.path.join(dst_folder, "__init__.py")
    if not os.path.exists(init):
        open(init, "w").close()
    dst = os.path.join(dst_folder, os.path.basename(src))
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.move(src, dst)
        print(f"  moved: {src} -> {dst}")
    elif os.path.exists(dst):
        print(f"  ok:    {dst}")

move("db.py",           "database")
move("base.py",         "scrapers")
move("reddit.py",       "scrapers")
move("rss.py",          "scrapers")
move("user.py",         "handlers")
move("job_pipeline.py", "services")
move("helpers.py",      "utils")

os.makedirs("data", exist_ok=True)
print("\nDone! Now run:")
print("  git add .")
print("  git commit -m 'fix: correct package folder structure'")
print("  git push")