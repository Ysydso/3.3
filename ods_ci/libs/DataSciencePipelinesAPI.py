import base64
import json
import os
import subprocess
import time
from json import JSONDecodeError

import requests
from robotlibcore import keyword
import requests
import base64
import json
import os
import subprocess
import time
from json.decoder import JSONDecodeError


class DataSciencePipelinesAPI:
    # init should not have a call to external system, otherwise dry-run will fail
    def __init__(self):
        self.route = ""
        self.sa_token = None

    @keyword
    def wait_until_openshift_pipelines_operator_is_deployed(self):
        """
        when creating at the first time, it can take like 1 minute to have the pods ready
        """
        deployment_count = 0
        count = 0
        while deployment_count != 1 and count < 30:
            deployments = []
            response, _ = self.run_oc(
                "oc get deployment -n openshift-operators openshift-pipelines-operator -o json"
            )
            try:
                response = json.loads(response)
                if (
                    response["metadata"]["name"] == "openshift-pipelines-operator"
                    and "readyReplicas" in response["status"]
                    and response["status"]["readyReplicas"] == 1
                ):
                    deployments.append(response)
            except JSONDecodeError:
                pass
            deployment_count = len(deployments)
            time.sleep(1)
            count += 1
        pipeline_run_crd_count = 0
        count = 0
        while pipeline_run_crd_count < 1 and count < 60:
            # https://github.com/opendatahub-io/odh-dashboard/issues/1673
            # It is possible to start the Pipeline Server without pipelineruns.tekton.dev CRD
            pipeline_run_crd_count = self.count_pods(
                "oc get crd pipelineruns.tekton.dev", 1
            )
            time.sleep(1)
            count += 1
        assert pipeline_run_crd_count == 1
        return self.count_running_pods(
            "oc get pods -n openshift-operators -l name=openshift-pipelines-operator -o json",
            "openshift-pipelines-operator",
            "Running",
            1,
        )

    @keyword
    def login_and_wait_dsp_route(
        self,
        user,
        pwd,
        project,
        route_name="ds-pipeline-pipelines-definition",
        class DataSciencePipelinesAPI:
            def __init__(self):
                self.sa_token = ""
                self.route = ""

            def fetch_token(self, user, pwd, timeout=120):
                print("Fetch token")
                basic_value = f"{user}:{pwd}".encode("ASCII")
                basic_value = base64.b64encode(basic_value).decode("ASCII")
                response = requests.get(
                    self.retrieve_auth_url(),
                    headers={"Authorization": f"Basic {basic_value}"},
                    verify=True,  # Enable server certificate validation
                    allow_redirects=False,
                )
                url_with_token = response.headers["Location"]
                access_token_key = "access_token="
                idx_token = url_with_token.index(access_token_key) + len(access_token_key)
                token = url_with_token[idx_token:]
                idx_token = token.index("&")
                self.sa_token = token[:idx_token]

                print("Fetch the dsp route")
                self.route = ""
                count = 0
                while self.route == "" and count < 60:
                    self.route, _ = self.run_oc(
                        f"oc get route -n {project} {route_name} --template={{{{.spec.host}}}}"
                    )
                    time.sleep(1)
                    count += 1

                assert self.route != "", "Route must not be empty"
                print(
                    f"Waiting for Data Science Pipeline route to be ready to avoid firing false alerts: {self.route}"
                )
                time.sleep(45)
                status = -1
                count = 0
                while status != 200 and count < timeout:
                    response, status = self.do_get(
                        f"https://{self.route}/apis/v1beta1/runs",
                        headers={"Authorization": f"Bearer {self.sa_token}"},
                        verify=True,  # Enable server certificate validation
                    )
                    # 503 -> service not deployed
                    # 504 -> service not ready
                    # if you need to debug, try to print also the response
                    print(f"({count}): Data Science Pipeline HTTP Status: {status}")
                    if status != 200:
                        time.sleep(30)
                        count += 30
                return status

            # Rest of the code...
