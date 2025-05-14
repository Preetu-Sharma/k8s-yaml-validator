"""
K8s YAML Validator Tool
-----------------------

This tool validates Kubernetes YAML files (single or combined multi-resource manifests)
for both required and recommended (non-required) fields.

Features:
- Supports validation for Pod, Deployment, Service, Ingress, PV, PVC, StatefulSet, DaemonSet, and StorageClass.
- Accepts both full resource types and shortcuts (e.g., 'po' for Pod, 'deploy' for Deployment).
- Detects YAML syntax errors.
- Validates resource-specific required fields.
- Warns about missing recommended best-practice fields.
- Supports both single-document and multi-document YAML files (separated by ---).
- Logs output with color-coded console messages.

Extensibility:
Further features can be added to support additional Kubernetes resource types
such as Job, CronJob, ConfigMap, Secret, and more.

Usage:
  python validator.py --path <file_or_folder> [--type <k8s_resource_type>]
  Use '--type all' to validate all supported resource types in multi-document YAMLs.
"""

import os
import time
import logging
import argparse
import yaml

# ANSI color codes for styled output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Logger
logger = logging.getLogger("K8s-YAML-Validator")
logger.setLevel(logging.INFO)

# Formatter
console = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler and set level
ch = logging.StreamHandler()
ch.setFormatter(console)
logger.addHandler(ch)


class Validator:
    def __init__(self, path, resource_type=None):
        """
        Initialize Validator with user-supplied path and optional resource type.
        """
        self.path = path
        self.resource_type = resource_type.lower() if resource_type else None
        self.files = []

    def add_yaml_file(self):
        """
        Populate the files list with YAML file paths from the provided path.
        """
        if os.path.isfile(self.path):
            self.files.append(self.path)
            logger.info(f"{GREEN}File added successfully for validation.{RESET}")
            print()
        elif os.path.isdir(self.path):
            for f in os.listdir(self.path):
                if f.endswith(".yaml") or f.endswith(".yml"):
                    self.files.append(os.path.join(self.path, f))
            logger.info(f"{GREEN}All Yaml files added from folder.{RESET}")
            print()
        else:
            logger.error(f"{YELLOW}provided name is neither a file nor a folder.{RESET}")
            print()

    def get_data(self):
        """
        Generator to read all documents from all YAML files.
        """
        for f in self.files:
            try:
                with open(f, "r") as file:
                    data = list(yaml.safe_load_all(file))
                    for index, doc in enumerate(data, 1):
                        yield f, index, doc
            except yaml.YAMLError:
                return
            except FileNotFoundError:
                return

    def check_yaml(self):
        """
        Validate all files for proper YAML syntax.
        """
        all_valid = True
        for f in self.files:
            try:
                with open(f, "r") as file:
                    print(f"{BLUE}Checking for YAML syntax in file...{RESET}")
                    print()
                    list(yaml.safe_load_all(file))
                time.sleep(2.0)
                logger.info(f"{GREEN} {f} YAML validation passed - No error found.{RESET}")
                print()
            except yaml.YAMLError as e:
                logger.error(f"{RED}YAML error while parsing {f}: {e}{RESET}")
                all_valid = False
                print()
            except FileNotFoundError as er:
                logger.error(f"{RED}File not found: {f}: {er}{RESET}")
                all_valid = False
                print()
        return all_valid

    def check_k8s_api_kind_name(self):
        """
        Ensure all YAML documents contain required K8s keys: apiVersion, kind, metadata.name.
        """
        for f, index, data in self.get_data():
            if not data:
                logger.error(f"{RED} {f} (doc #{index}) is invalid{RESET}")
                print()
                return False

            api = data.get("apiVersion")
            kind = data.get("kind")
            name = data.get("metadata", {}).get("name")

            if not all([api, kind, name]):
                logger.error(f"{RED} {f} (doc #{index}): Missing required fields apiVersion, kind or metadata.name"
                             f"{RESET}")
                print()
                return False

        return True

    def check_k8s_pod(self):
        """
        Validates required and recommended fields for Pod resources.
        """
        if self.check_k8s_api_kind_name():
            valid = True
            for f, index, data in self.get_data():
                if data.get("kind", "") == "Pod":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    containers = data.get("spec", {}).get("containers", [])

                    # Non-required/recommended fields
                    restart_policy = data.get("spec", {}).get("restartPolicy")
                    node_selector = data.get("spec", {}).get("nodeSelector")
                    tolerations = data.get("spec", {}).get("tolerations")
                    security_context = data.get("spec", {}).get("securityContext")

                    for c in containers:
                        resources = c.get("resources", {})
                        requests = resources.get("requests")
                        limits = resources.get("limits")

                        if not requests:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.requests' is missing from Pod spec.{RESET}")
                        if not limits:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.limits' is missing from Pod spec.{RESET}")
                    if not security_context:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'securityContext' is missing from Pod spec.{RESET}")
                    if not tolerations:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'tolerations' is missing from Pod spec.{RESET}")
                    if not node_selector:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'nodeSelector' is missing from Pod spec.{RESET}")
                    if not restart_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'restartPolicy' is missing from Pod spec.{RESET}")

                    if not containers or not all(c.get("image") and c.get("name") for c in containers):
                        logger.error(f"{RED} {f} (doc #{index}): required field - Pod must have containers with"
                                     f" name and image.{RESET}")
                        valid = False
                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required "
                                    f"fields in Pod spec are present.{RESET}")
                        print()
                else:
                    continue

    def check_k8s_deployment(self):
        """
        Validates required and recommended fields for Deployment resources.
        """
        if self.check_k8s_api_kind_name():
            valid = True
            for f, index, data in self.get_data():
                if data.get("kind", "") == "Deployment":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    replicas = data.get("spec", {}).get("replicas")
                    selector = data.get("spec", {}).get("selector", {}).get("matchLabels")
                    template_labels = data.get("spec", {}).get("template", {}).get("metadata", {}).get("labels")
                    containers = data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

                    # Non-required/recommended fields
                    strategy = data.get("spec", {}).get("strategy")
                    restart_policy = data.get("spec", {}).get("template", {}).get("spec", {}).get("restartPolicy")
                    node_selector = data.get("spec", {}).get("template", {}).get("spec", {}).get("nodeSelector")
                    tolerations = data.get("spec", {}).get("template", {}).get("spec", {}).get("tolerations")
                    security_context = data.get("spec", {}).get("template", {}).get("spec", {}).get("securityContext")
                    for c in containers:
                        resources = c.get("resources", {})
                        requests = resources.get("requests")
                        limits = resources.get("limits")

                        if not requests:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.requests' is missing from Deployment spec.{RESET}")
                        if not limits:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.limits' is missing from Deployment spec.{RESET}")

                    if not strategy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'strategy' is missing from Deployment spec.{RESET}")
                    if not security_context:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'securityContext' is missing from Deployment spec.{RESET}")
                    if not tolerations:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'tolerations' is missing from Deployment spec.{RESET}")
                    if not node_selector:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'nodeSelector' is missing from Deployment spec.{RESET}")
                    if not restart_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'restartPolicy' is missing from Deployment spec.{RESET}")

                    if not replicas:
                        logger.error(f"{RED} {f} (doc #{index}): required field - 'replicas' is missing from"
                                     f" Deployment spec.{RESET}")
                        valid = False
                    if not selector:
                        logger.error(f"{RED} {f} (doc #{index}): required field - 'matchLabels' is missing from"
                                     f" Deployment spec.{RESET}")
                        valid = False
                    if not template_labels:
                        logger.error(f"{RED} {f} (doc #{index}): required field - 'labels' is missing from"
                                     f" Deployment spec.{RESET}")
                        valid = False
                    if not containers or not all(c.get("image") and c.get("name") for c in containers):
                        logger.error(f"{RED} {f} (doc #{index}): required field - Pod must have containers"
                                     f" with name and image.{RESET}")
                        valid = False

                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in Deployment spec are present.{RESET}")
                        print()

                else:
                    continue

    def check_k8s_service(self):
        """
        Validates required and recommended fields for Service resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "Service":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    selector = data.get("spec", {}).get("selector")
                    ports = data.get("spec", {}).get("ports", [])
                    # Non-required/recommended fields
                    type_ = data.get("spec", {}).get("type")
                    session_affinity = data.get("spec", {}).get("sessionAffinity")
                    external_traffic_policy = data.get("spec", {}).get("externalTrafficPolicy")

                    if not type_:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'type' is missing from Service spec.{RESET}")
                    if not session_affinity:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'sessionAffinity' is missing from Service spec.{RESET}")
                    if not external_traffic_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'externalTrafficPolicy' is missing from Service spec.{RESET}")

                    if not selector:
                        logger.error(f"{RED} {f} (doc #{index}): required field - selector "
                                     f"field is not available in service{RESET}")
                        valid = False
                    if not ports or not all(port.get("port") and port.get("targetPort") for port in ports):
                        logger.error(f"{RED} {f} (doc #{index}): required field - Service "
                                     f"must have port with targetPort.{RESET}")
                        valid = False

                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in Service spec are present.{RESET}")
                        print()

                else:
                    continue

    def check_k8s_ingress(self):
        """
        Validates required and recommended fields for Ingress resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "Ingress":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Non-required/recommended fields
                    annotations = data.get("metadata", {}).get("annotations")
                    tls = data.get("spec", {}).get("tls")
                    # Required Fields
                    rules = data.get("spec", {}).get("rules", [])
                    if not annotations:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'annotations' is missing from Ingress.{RESET}")
                    if not tls:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'tls' is missing from Ingress spec.{RESET}")

                    if not rules:
                        logger.error(f"{RED} {f} (doc #{index}): required field - Ingress rules "
                                     f"field is not available in Ingress{RESET}")
                        valid = False
                    else:
                        for rule in rules:
                            paths = rule.get("http", {}).get("paths", [])
                            if not paths:
                                logger.error(f"{RED} {f} (doc #{index}): required field - Ingress rule has"
                                             f" no paths defined{RESET}")
                                valid = False
                            for path in paths:
                                path_type = path.get("pathType")
                                backend = path.get("backend")
                                if not backend:
                                    logger.error(
                                        f"{RED} {f} (doc #{index}): required field - backend is missing"
                                        f" in Ingress path{RESET}")
                                    valid = False
                                    continue

                                service = backend.get("service")
                                if not service:
                                    logger.error(
                                        f"{RED} {f} (doc #{index}): required field - backend.service is"
                                        f" missing in Ingress path{RESET}")
                                    valid = False
                                    continue

                                name = service.get("name")
                                port = service.get("port")
                                port_number = port.get("number") if isinstance(port, dict) else port
                                if not (path_type and name and port and port_number):
                                    logger.error(
                                        f"{RED} {f} (doc #{index}): required field - pathType, service name, or"
                                        f" port.number is missing in Ingress"
                                        f"{RESET}")
                                    valid = False
                                if not isinstance(port, dict):
                                    logger.warning(
                                        f"{YELLOW} {f} (doc #{index}): In Ingress Service Port is not a structured"
                                        f" object; using shorthand format{RESET}")

                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in Ingress spec are present.{RESET}")
                        print()

                else:
                    continue

    def check_pv(self):
        """
        Validates required and recommended fields for PersistentVolume resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "PersistentVolume":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    storage_sz = data.get("spec", {}).get("capacity", {}).get("storage")
                    access_modes = data.get("spec", {}).get("accessModes")
                    sc = data.get("spec", {}).get("storageClassName")

                    # Non-required/recommended fields
                    reclaim_policy = data.get("spec", {}).get("persistentVolumeReclaimPolicy")
                    volume_mode = data.get("spec", {}).get("volumeMode")
                    if not reclaim_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'persistentVolumeReclaimPolicy' is missing from pv spec.{RESET}")
                    if not volume_mode:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'volumeMode' is missing from pv spec.{RESET}")

                    if not storage_sz:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pv has no storage size defined{RESET}")
                        valid = False
                    if not access_modes:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pv has no accessModes defined{RESET}")
                        valid = False
                    if not sc:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pv has no storageClassName defined{RESET}")
                        valid = False
                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in pv spec are present.{RESET}")
                        print()
                else:
                    continue

    def check_pvc(self):
        """
        Validates required and recommended fields for PersistentVolumeClaim resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "PersistentVolumeClaim":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    access_modes = data.get("spec", {}).get("accessModes")
                    requests = data.get("spec", {}).get("resources", {}).get("requests")
                    # Non-required/recommended fields
                    volume_mode = data.get("spec", {}).get("volumeMode")
                    if isinstance(requests, dict):
                        storage_rq = requests.get("storage")
                    else:
                        storage_rq = None
                    sc = data.get("spec", {}).get("storageClassName")
                    if not volume_mode:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f" 'volumeMode' is missing from pvc spec.{RESET}")

                    if not access_modes:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pvc has no accessModes defined{RESET}")
                        valid = False
                    if not storage_rq:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pvc has no requests storage defined{RESET}")
                        valid = False
                    if not sc:
                        logger.error(f"{RED} {f} (doc #{index}): required field - pv has no storageClassName defined{RESET}")
                        valid = False
                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in pvc spec are present.{RESET}")
                        print()
                else:
                    continue

    def check_sc(self):
        """
        Validates required and recommended fields for StorageClass resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "StorageClass":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    provisioner = data.get("provisioner")
                    # Non-required/recommended fields
                    reclaim_policy = data.get("reclaimPolicy")
                    volume_binding_mode = data.get("volumeBindingMode")
                    allow_volume_expansion = data.get("allowVolumeExpansion")
                    parameters = data.get("parameters")
                    if not reclaim_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'reclaimPolicy' is missing from sc.{RESET}")
                    if not volume_binding_mode:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'volumeBindingMode' is missing from sc.{RESET}")
                    if not allow_volume_expansion:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'parameters' is missing from sc.{RESET}")
                    if not parameters:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'volumeMode' is missing from sc.{RESET}")
                    if not provisioner:
                        logger.error(f"{RED} {f} (doc #{index}): required field - sc has no provisioner defined{RESET}")
                        valid = False
                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in sc are present.{RESET}")
                        print()
                else:
                    continue

    def check_ds(self):
        """
        Validates required and recommended fields for DaemonSet resources.
        """
        if self.check_k8s_api_kind_name():
            for f, index, data in self.get_data():
                valid = True
                if data.get("kind", "") == "DaemonSet":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    selector = data.get("spec", {}).get("selector", {}).get("matchLabels")
                    template_labels = data.get("spec", {}).get("template", {}).get("metadata", {}).get("labels")
                    containers = data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

                    # Non-required/recommended fields
                    update_strategy = data.get("spec", {}).get("updateStrategy")
                    restart_policy = data.get("spec", {}).get("template", {}).get("spec", {}).get("restartPolicy")
                    node_selector = data.get("spec", {}).get("template", {}).get("spec", {}).get("nodeSelector")
                    tolerations = data.get("spec", {}).get("template", {}).get("spec", {}).get("tolerations")
                    security_context = data.get("spec", {}).get("template", {}).get("spec", {}).get("securityContext")

                    for c in containers:
                        resources = c.get("resources", {})
                        requests = resources.get("requests")
                        limits = resources.get("limits")

                        if not requests:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.requests' is missing from DaemonSet spec.{RESET}")
                        if not limits:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.limits' is missing from DaemonSet spec.{RESET}")

                    if not update_strategy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'updateStrategy' is missing from DaemonSet spec.{RESET}")
                    if not security_context:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'securityContext' is missing from DaemonSet spec.{RESET}")
                    if not tolerations:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'tolerations' is missing from DaemonSet spec.{RESET}")
                    if not node_selector:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'nodeSelector' is missing from DaemonSet spec.{RESET}")
                    if not restart_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'restartPolicy' is missing from DaemonSet spec.{RESET}")

                    if not selector:
                        logger.error(f"{RED} {f} (doc #{index}): required field - selector field is not"
                                     f" available in ds{RESET}")
                        valid = False
                    if not template_labels:
                        logger.error(
                            f"{RED} {f} (doc #{index}): required field - pod template labels field is not"
                            f" available in ds{RESET}")
                        valid = False
                    if not containers or not all(c.get("image") and c.get("name") for c in containers):
                        logger.error(f"{RED} {f} (doc #{index}): required field - Pod must have containers"
                                     f" with name and image{RESET}")
                        valid = False

                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields"
                                    f" in DaemonSet spec are present.{RESET}")
                        print()

                else:
                    continue

    def check_k8s_sts(self):
        """
        Validates required and recommended fields for StatefulSet resources.
        """
        if self.check_k8s_api_kind_name():
            valid = True
            for f, index, data in self.get_data():
                if data.get("kind", "") == "StatefulSet":
                    print(f"{BLUE}Validating K8s resource type {data.get("kind", "")} in file...{RESET}")
                    print()
                    time.sleep(2.0)
                    # Required Fields
                    replicas = data.get("spec", {}).get("replicas")
                    service_name = data.get("spec", {}).get("serviceName")
                    selector = data.get("spec", {}).get("selector", {}).get("matchLabels")
                    template_labels = data.get("spec", {}).get("template", {}).get("metadata", {}).get("labels")
                    containers = data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])

                    # Non-required/recommended fields
                    volume_claim_templates = data.get("spec", {}).get("volumeClaimTemplates")
                    pod_mgmt_policy = data.get("spec", {}).get("podManagementPolicy")
                    update_strategy = data.get("spec", {}).get("updateStrategy")
                    restart_policy = data.get("spec", {}).get("template", {}).get("spec", {}).get("restartPolicy")
                    node_selector = data.get("spec", {}).get("template", {}).get("spec", {}).get("nodeSelector")
                    tolerations = data.get("spec", {}).get("template", {}).get("spec", {}).get("tolerations")
                    security_context = data.get("spec", {}).get("template", {}).get("spec", {}).get("securityContext")

                    for c in containers:
                        resources = c.get("resources", {})
                        requests = resources.get("requests")
                        limits = resources.get("limits")

                        if not requests:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.requests' is missing from StatefulSet spec.{RESET}")
                        if not limits:
                            logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                           f"'resources.limits' is missing from StatefulSet spec.{RESET}")

                    if not volume_claim_templates:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'volumeClaimTemplates' is missing from StatefulSet spec.{RESET}")
                    if not pod_mgmt_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'podManagementPolicy' is missing from StatefulSet spec.{RESET}")
                    if not update_strategy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'updateStrategy' is missing from StatefulSet spec.{RESET}")
                    if not security_context:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'securityContext' is missing from StatefulSet spec.{RESET}")
                    if not tolerations:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'tolerations' is missing from StatefulSet spec.{RESET}")
                    if not node_selector:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'nodeSelector' is missing from StatefulSet spec.{RESET}")
                    if not restart_policy:
                        logger.warning(f"{YELLOW} {f} (doc #{index}): non-required/recommended field - "
                                       f"'restartPolicy' is missing from StatefulSet spec.{RESET}")

                    if not replicas:
                        logger.error(f"{RED} {f} (doc #{index}): required field - replicas field is not"
                                     f" available in sts{RESET}")
                        valid = False
                    if not service_name:
                        logger.error(f"{RED} {f} (doc #{index}): required field - serviceName field is"
                                     f" not available in sts{RESET}")
                        valid = False
                    if not selector:
                        logger.error(f"{RED} {f} (doc #{index}): required field - selector field is not"
                                     f" available in sts {RESET}")
                        valid = False
                    if not template_labels:
                        logger.error(
                            f"{RED} {f} (doc #{index}): required field -  pod template labels field is"
                            f" not available in sts{RESET}")
                        valid = False
                    if not containers or not all(c.get("image") and c.get("name") for c in containers):
                        logger.error(f"{RED} {f} (doc #{index}): required field -  Pod must have containers"
                                     f" with name and image.{RESET}")
                        valid = False

                    if valid:
                        logger.info(f"{GREEN} {f} (doc #{index}): K8s validation passed: all required fields for this"
                                    f" in StatefulSet spec are present.{RESET}")
                        print()

                else:
                    continue

    def __str__(self):
        """
        Print total validated documents.
        """
        num_files = len(self.files)
        return f"{GREEN}Validation complete. Total YAML documents checked: {num_files}{RESET}"

    def all(self):
        """
        Run all validators if --type all is passed.
        """
        print(f"{BLUE}Running validation for all supported Kubernetes resource types...{RESET}")
        time.sleep(2.0)
        self.check_k8s_pod()
        self.check_k8s_deployment()
        self.check_k8s_service()
        self.check_k8s_ingress()
        self.check_pv()
        self.check_pvc()
        self.check_k8s_sts()
        self.check_ds()
        self.check_sc()

    def run(self):
        """
        Dispatcher to call validation method based on the resource type.
        """
        data_found = False
        for _ in self.get_data():
            data_found = True
            break

        if not data_found:
            logger.error(f"{RED}❌ No valid YAML documents found. Skipping K8s validation.{RESET}")
            return
        if self.resource_type:
            if self.resource_type == "pod" or self.resource_type == "po":
                self.check_k8s_pod()
            elif self.resource_type == "deployment" or self.resource_type == "deploy":
                self.check_k8s_deployment()
            elif self.resource_type == "service" or self.resource_type == "svc":
                self.check_k8s_service()
            elif self.resource_type == "ingress" or self.resource_type == "ing":
                self.check_k8s_ingress()
            elif self.resource_type == "persistentvolume" or self.resource_type == "pv":
                self.check_pv()
            elif self.resource_type == "persistentvolumeclaim" or self.resource_type == "pvc":
                self.check_pvc()
            elif self.resource_type == "statefulset" or self.resource_type == "sts":
                self.check_k8s_sts()
            elif self.resource_type == "daemonset" or self.resource_type == "ds":
                self.check_ds()
            elif self.resource_type == "storageclass" or self.resource_type == "sc":
                self.check_sc()
            elif self.resource_type == "all":
                self.all()
            else:
                logger.error(f"{RED} Please enter a valid k8s resource type{RESET}")


# CLI Argument Parsing
parser = argparse.ArgumentParser(
    prog='K8s-YAML-Validator',
    usage=(
        "%(prog)s --path <file_or_directory> [--type <resource_type>]\n\n"
        "Description:\n"
        "  Validates Kubernetes YAML files, including multi-document YAMLs (combined manifests)\n"
        "  with multiple resources separated by '---'. For example: PersistentVolume, PVC,\n"
        "  and Deployment in a single file.\n\n"
        "Usage Notes:\n"
        "  - Use --type <resource_type> to validate a specific kind (e.g., pod, deployment, pvc).\n"
        "  - Use --type <all> to validate each document in combined multi-resource YAML files.\n"
        "  - Supported types: pod, deployment, service, ingress, pv, pvc, statefulset, daemonset, storageclass, all.\n"
    ),
    description="K8s YAML Validator - Validates required and recommended fields in Kubernetes manifests."
)

parser.add_argument(
    "--path",
    required=True,
    help="Path to a YAML file or a directory containing multiple .yaml/.yml files. "
         "Supports both single-resource and combined multi-resource manifests."
)

parser.add_argument(
    "--type",
    help="Kubernetes resource type to validate (e.g., pod, deployment, service, pvc, etc.).\n"
         "Use 'all' to validate every resource in combined YAMLs. This is optional but recommended "
         "for more specific validation."
)

# Run the tool
args = parser.parse_args()
y1 = Validator(args.path, args.type)
y1.add_yaml_file()
y1.check_yaml()
y1.run()
print(y1)
