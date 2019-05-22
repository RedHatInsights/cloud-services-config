set -e
rm -rf venv || true
python3 -m venv ./venv
source ./venv/bin/activate
python -m pip install -r requirements.txt
python3 update_api.py