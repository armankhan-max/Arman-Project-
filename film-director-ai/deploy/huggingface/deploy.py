"""Upload this project to a Hugging Face Docker Space.  Usage: HF_TOKEN=... python deploy/huggingface/deploy.py <user>/<space>"""
import os
import shutil
import sys
import tempfile

from huggingface_hub import HfApi

repo = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
api = HfApi(token=os.environ.get("HF_TOKEN"))
api.create_repo(repo, repo_type="space", space_sdk="docker", exist_ok=True, private=False)
for k in ("FDA_SECRET_KEY", "FDA_OWNER_PASSWORD"):
    if os.environ.get(k):
        api.add_space_secret(repo, k, os.environ[k])
d = tempfile.mkdtemp()
for part in ("backend", "frontend", "infra"):
    shutil.copytree(os.path.join(root, part), os.path.join(d, part),
                    ignore=shutil.ignore_patterns("node_modules", ".next", "out", "__pycache__", "*.pyc", "tests", ".pytest_cache", "tsconfig.tsbuildinfo"))
shutil.copy(os.path.join(root, "deploy", "huggingface", "Dockerfile"), os.path.join(d, "Dockerfile"))
shutil.copy(os.path.join(root, "deploy", "huggingface", "README.md"), os.path.join(d, "README.md"))
api.upload_folder(folder_path=d, repo_id=repo, repo_type="space", commit_message="Deploy Film Director AI")
print("https://%s.hf.space" % repo.replace("/", "-").replace("_", "-").lower())
