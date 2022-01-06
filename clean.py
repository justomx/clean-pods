import json
import os
from datetime import datetime, timedelta

import requests

# --- Variables ---------------------------------------------------------------
# Get the token for authenticate via the API
if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
    token = (
        open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
        .read()
        .replace("\n", "")
    )
else:
    token = os.environ["TOKEN"]

# API URL. Ex. https://kubernetes.default.svc/api/
apiURL = os.environ.get("API_URL", "https://kubernetes.default.svc/")

# Namespace where the pods are running
namespace = os.environ.get("NAMESPACE", "default")

# get HPA to patch
hpa_list = json.loads(os.environ.get("HPA_LIST", "{}"))

# --- Functions ---------------------------------------------------------------
def callAPI(method, url, body):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/merge-patch+json",
    }
    requests.packages.urllib3.disable_warnings()
    request = requests.request(
        method, url, headers=headers, verify=False, data=json.dumps(body)
    )
    return request.json()


def getHPA(namespace):
    url = (
        apiURL
        + "apis/autoscaling/v1/namespaces/"
        + namespace
        + "/horizontalpodautoscalers/"
    )
    response = callAPI("GET", url, "")
    hpa = []
    for i in response["items"]:
        hpa.append(i["metadata"]["name"])
    return hpa


def patchHPA(namespace, hpa_name, hpa_minReplicas):
    url = (
        apiURL
        + "apis/autoscaling/v1/namespaces/"
        + namespace
        + "/horizontalpodautoscalers/"
        + hpa_name
    )
    response = callAPI("PATCH", url, body={"spec": {"minReplicas": hpa_minReplicas}})
    return response["status"]


# --- Main
current_hpa = getHPA(namespace)

if hpa_list:
    for name in hpa_list:
        if name in current_hpa:
            status = patchHPA(namespace, name, hpa_list[name]["minReplicas"])
            print(f"{name} - {status}")
