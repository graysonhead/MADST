from app import db, models
from . import connectwise as cw
import cwcreds
'''First, build a list of companies from CW'''


cwapi = cw.ConnectWiseApi(cwUrl=cwcreds.cwUrl, cwHeaders=cwcreds.cwHeaders)
