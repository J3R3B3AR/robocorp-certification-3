from robocorp import workitems
from robocorp.tasks import task
from RPA.HTTP import HTTP
from RPA.JSON import JSON
from RPA.Tables import Tables


http = HTTP()
json_lib = JSON()
table_lib = Tables()

TRAFFIC_JSON_FILE_PATH = "output/traffic.json"
COUNTRY_KEY = "SpatialDim"
YEAR_KEY = "TimeDim"
RATE_KEY = "NumericValue"
GENDER_KEY = "Dim1"
MAX_FATALITY_RATE = 5.0
BOTH_GENDERS = "BTSX"


@task
def produce_traffic_data():
    """
    Downloads WHO traffic fatality data, filters to low-rate countries,
    deduplicates to latest year per country, and outputs work items
    for the consumer task.
    """
    http.download(
        url="https://github.com/robocorp/inhuman-insurance-inc/raw/main/RS_198.json",
        target_file=TRAFFIC_JSON_FILE_PATH,
        overwrite=True,
    )
    traffic_data = load_traffic_data_as_table()
    filtered_data = filter_and_sort_traffic_data(traffic_data)
    filtered_data = get_latest_data_by_country(filtered_data)
    payloads = create_work_item_payloads(filtered_data)
    save_work_item_payloads(payloads)


def load_traffic_data_as_table():
    json_data = json_lib.load_json_from_file(TRAFFIC_JSON_FILE_PATH)
    return table_lib.create_table(json_data["value"])


def filter_and_sort_traffic_data(data):
    table_lib.filter_table_by_column(data, RATE_KEY, "<", MAX_FATALITY_RATE)
    table_lib.filter_table_by_column(data, GENDER_KEY, "==", BOTH_GENDERS)
    table_lib.sort_table_by_column(data, YEAR_KEY, False)
    return data


def get_latest_data_by_country(data):
    grouped = table_lib.group_table_by_column(data, COUNTRY_KEY)
    latest = []
    for group in grouped:
        first_row = table_lib.pop_table_row(group)
        latest.append(first_row)
    return latest


def create_work_item_payloads(traffic_data):
    payloads = []
    for row in traffic_data:
        payload = dict(
            country=row[COUNTRY_KEY],
            year=row[YEAR_KEY],
            rate=row[RATE_KEY],
        )
        payloads.append(payload)
    return payloads


def save_work_item_payloads(payloads):
    for payload in payloads:
        workitems.outputs.create(dict(traffic_data=payload))
