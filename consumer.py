import requests
from robocorp import workitems
from robocorp.tasks import task


SALES_SYSTEM_API_URL = "https://robocorp.com/inhuman-insurance-inc/sales-system-api"


@task
def consume_traffic_data():
    """
    Reads work items produced by the producer task, validates each
    country code, and posts valid records to the sales system API.
    Marks items done or failed with typed exception codes.
    """
    for item in workitems.inputs:
        traffic_data = item.payload["traffic_data"]
        if validate_traffic_data(traffic_data):
            status, return_json = post_traffic_data_to_sales_system(traffic_data)
            if status == 200:
                item.done()
            else:
                item.fail(
                    exception_type="APPLICATION",
                    code="TRAFFIC_DATA_POST_FAILED",
                    message=return_json.get("message", "Unknown API error"),
                )
        else:
            item.fail(
                exception_type="BUSINESS",
                code="INVALID_TRAFFIC_DATA",
                message=f"Invalid country code in payload: {item.payload}",
            )


def validate_traffic_data(traffic_data):
    """Returns True if the country code is exactly 3 characters."""
    return len(traffic_data["country"]) == 3


def post_traffic_data_to_sales_system(traffic_data):
    """POSTs traffic data to the sales system and returns (status_code, json)."""
    response = requests.post(SALES_SYSTEM_API_URL, json=traffic_data)
    return response.status_code, response.json()
