import yaml

from backend.tinvest_api import functions
from backend.utils import params

with open(params.tinvest_api_token, "r") as f:
    TOKEN = yaml.safe_load(f)["token"]
