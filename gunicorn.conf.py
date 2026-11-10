import os


bind = f"0.0.0.0:{int(os.environ.get('PORT', '8000'))}"
workers = 2
accesslog = "-"
errorlog = "-"