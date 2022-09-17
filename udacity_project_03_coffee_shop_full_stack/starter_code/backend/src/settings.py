from dotenv import load_dotenv
import os
load_dotenv()
DB_NAME = os.environ.get("DB_NAME")
AUTH0_TENANT_DOMAIN = os.environ.get("AUTH0_TENANT_DOMAIN")
AUTH0_ALGORITHMS = os.environ.get("AUTH0_ALGORITHMS")
AUTH0_API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE")