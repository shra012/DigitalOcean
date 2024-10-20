import os, time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Get API Tokens from environment variables
TERRAFORM_API_TOKEN = os.getenv('TFC_TOKEN')
DIGITALOCEAN_API_TOKEN = os.getenv('DIGITALOCEAN_TOKEN')

DIGITALOCEAN_API_URL = "https://api.digitalocean.com/v2"
TERRAFORM_API_URL = f"https://app.terraform.io/api/v2"


# Helper function to retry requests
def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=None):
    session = requests.Session()
    if status_forcelist is None:
        status_forcelist = list(range(300, 600))  # Retry on all 3xx, 4xx, and 5xx codes
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


# Get Workspace ID using workspace name
def get_workspace_id(workspace_name):
    url = f"{TERRAFORM_API_URL}/organizations/digitalocean-shra012/workspaces/{workspace_name}"
    headers = {
        "Authorization": f"Bearer {TERRAFORM_API_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    response = requests_retry_session().get(url, headers=headers)

    if response.status_code == 200:
        workspace_id = response.json()["data"]["id"]
        print(f"Workspace ID: {workspace_id}")
        return workspace_id
    else:
        print(f"Failed to fetch workspace ID: {response.text}")
        return None


# Get the current state version and its outputs for the workspace
def get_workspace_outputs(workspace_id):
    print("Fetching the current state version and outputs...")
    url = f"{TERRAFORM_API_URL}/workspaces/{workspace_id}/current-state-version?include=outputs"
    headers = {
        "Authorization": f"Bearer {TERRAFORM_API_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    response = requests_retry_session().get(url, headers=headers)

    if response.status_code == 200:
        if "included" in response.json():
            outputs = response.json()["included"]
            for output in outputs:
                if output["attributes"]["name"] == "droplet_id":
                    droplet_id = output["attributes"]["value"]
                    print(f"Found droplet_id: {droplet_id}")
                    return droplet_id
            print("No droplet_id found in the outputs.")
            return None
        else:
            print("No outputs found in the included list.")
            return None
    else:
        print(f"Failed to fetch outputs: {response.text}")
        return None


# Check if the Droplet exists by ID
def droplet_exists(droplet_id):
    print(f"Checking if droplet with ID '{droplet_id}' exists...")
    url = f"{DIGITALOCEAN_API_URL}/droplets/{droplet_id}"
    headers = {
        "Authorization": f"Bearer {DIGITALOCEAN_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests_retry_session().get(url, headers=headers)

    if response.status_code == 200:
        print(f"Droplet with ID '{droplet_id}' exists.")
        return True
    elif response.status_code == 404:
        print(f"Droplet with ID '{droplet_id}' not found.")
        return False
    else:
        print(f"Failed to check droplet existence: {response.text}")
        return False


# Function to trigger a snapshot creation by applying to terraform with create_snapshot=true
def apply_terraform(workspace_id, is_destroy=False):
    print("Inside apply terraform...")
    url = f"{TERRAFORM_API_URL}/runs"
    headers = {
        "Authorization": f"Bearer {TERRAFORM_API_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    data = {
        "data": {
            "attributes": {
                "message": "Create snapshot before destroy",
                "is-destroy": is_destroy,
                "auto-apply": True,  # Set to True if you want auto-apply
                "variables": [
                    {"key": "do_token", "value": f'"{DIGITALOCEAN_API_TOKEN}"', "category": "terraform",
                     "sensitive": True}
                ]
            },
            "type": "runs",
            "relationships": {
                "workspace": {
                    "data": {
                        "type": "workspaces",
                        "id": workspace_id
                    }
                }
            }
        }
    }

    response = requests_retry_session().post(url, headers=headers, json=data)

    if response.status_code == 201:
        run_id = response.json()["data"]["id"]
        print(f"Apply run triggered successfully (Run ID: {run_id})")
        return run_id
    else:
        print(f"Failed to trigger snapshot creation: {response.text}")
        return None


# Fetch the log-read URL from the plan
def print_log(plan_or_apply_id, plan_or_apply_type="plans"):
    url = f"{TERRAFORM_API_URL}/{plan_or_apply_type}/{plan_or_apply_id}"
    headers = {
        "Authorization": f"Bearer {TERRAFORM_API_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        plan_data = response.json()
        log_read_url = plan_data["data"]["attributes"]["log-read-url"]
        print(f"Log read URL: {log_read_url}")
    else:
        print(f"Failed to fetch log read URL for {plan_or_apply_type} details")


def is_terraform_run_successful(run_id, max_retries=10, interval=30):
    """
    Poll the Terraform Cloud API for the status of a run until it is completed or fails.

    :param run_id: The ID of the Terraform run to poll.
    :param max_retries: The maximum number of polling attempts.
    :param interval: The wait time between polling attempts in seconds.
    :return: True if the run was successful, False if it failed or was canceled.
    """
    url = f"{TERRAFORM_API_URL}/runs/{run_id}"
    headers = {
        "Authorization": f"Bearer {TERRAFORM_API_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            run_data = response.json()
            run_status = run_data["data"]["attributes"]["status"]
            print(f"Attempt {attempt + 1}: Run status is '{run_status}'")

            if run_status == "applied":
                apply_id = run_data["data"]["relationships"]["apply"]["data"]["id"]
                print_log(apply_id, plan_or_apply_type="applies")
                return True
            elif run_status in ["errored", "canceled"]:
                plan_id = run_data["data"]["relationships"]["plan"]["data"]["id"]
                print_log(plan_id, plan_or_apply_type="plans")
                print(f"Run {run_id} failed with status '{run_status}'.")
                return False

        else:
            print(f"Error fetching run status: {response.text}")
            return False

        # Wait for the specified interval before the next attempt
        time.sleep(interval)

    print(f"Max retries reached for polling run {run_id}")
    return False


# Main function
def main(event, context):
    start_time = time.time()
    print("Starting the snapshot creation and destroy process...")
    droplet_name = event.get("droplet_name", None)
    if droplet_name is None:
        print("droplet_name is required. Aborting operations.")
        return handle_response("droplet_name is required", start_time)
    # Step 1: Get the workspace ID
    droplet_workspace_id = get_workspace_id("development-droplet")
    if not droplet_workspace_id:
        return handle_response("Workspace ID not found", start_time)

    # Step 2: Get the last successful Terraform run's outputs and extract the droplet_id
    droplet_id = get_workspace_outputs(droplet_workspace_id)
    if droplet_id is None:
        print("No droplet_id found in the Terraform outputs. Aborting operations.")
        return handle_response("Droplet ID not found", start_time)

    # Step 3: Check if the droplet exists in DigitalOcean
    if not droplet_exists(droplet_id):
        print(f"Droplet with ID {droplet_id} does not exist. Aborting operations.")
        return handle_response("Droplet not found", start_time)

    # Step 4: Get the workspace ID
    snapshot_workspace_id = get_workspace_id("development-snapshot")
    if not droplet_workspace_id:
        return handle_response("Workspace ID not found", start_time)

    # Step 5: Apply Terraform to create a snapshot
    print(f"Creating snapshot via Terraform...")
    snapshot_run_id = apply_terraform(snapshot_workspace_id)
    if snapshot_run_id and is_terraform_run_successful(run_id=snapshot_run_id):
        print(f"Snapshot creation ran successfully (Run ID: {snapshot_run_id})")
    else:
        print("Snapshot creation failed.")

    # Step 6: Apply Terraform to destroy the droplet
    print(f"Droplet destroy via Terraform...")
    destroy_run_id = apply_terraform(droplet_workspace_id, True)
    if destroy_run_id:
        print(f"Destroy ran successfully (Run ID: {destroy_run_id})")
    else:
        print("Droplet destroy failed.")

    return handle_response("done", start_time)


def handle_response(response, start_time):
    print(f"Function runtime: {time.time() - start_time:.2f} seconds")
    return {"status": response}
