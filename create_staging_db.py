#!/usr/bin/env python3
"""
Create staging database for environment testing
"""

import os
import sys

sys.path.append("src")

from database import init_db

# Set environment for staging
os.environ["DATABASE_URL"] = "sqlite:///data/staging_guestbook.db"
os.environ["ENVIRONMENT"] = "staging"

print("Creating staging database...")
init_db()
print("Staging database created: data/staging_guestbook.db")
