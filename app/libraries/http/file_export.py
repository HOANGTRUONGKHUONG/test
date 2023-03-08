import flask_excel as excel
from flask import Flask

app = Flask(__name__)
excel.init_excel(app)


def monitor_export_data(data, file_name="export_data"):
    return excel.make_response_from_records(data, "csv", file_name=file_name)
