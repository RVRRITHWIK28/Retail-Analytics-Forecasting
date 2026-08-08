import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    DATABASE_URL = "postgresql://neondb_owner:npg_xAMJw4FeXWR2@ep-empty-bird-axduhfyz-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)