#!/usr/bin/env bash

set -o errexit # Exit on error

pip install -r requirements.txt

python3 - << 'EOF'
import ssl
print(ssl.get_default_verify_paths())
EOF

python manage.py collectstatic --noinput
python manage.py migrate