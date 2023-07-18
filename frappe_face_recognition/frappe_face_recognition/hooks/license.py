import random
import string
from datetime import datetime

def beforeValidate(doc, method=None):
    current_year_month = datetime.now().strftime("%y%m")
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    doc.license_code = f"{current_year_month}-{random_code[:4]}-{random_code[4:]}"