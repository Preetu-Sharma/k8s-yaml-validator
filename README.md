# 🚀 Kubernetes YAML Validator Tool

A powerful yet lightweight Python CLI tool to **validate Kubernetes YAML files** (single or multi-resource) for required and recommended best practices.

---

## ✅ Features

- 🔍 **YAML Syntax Validation** – Detects parsing errors in YAML format.
- 🧩 **Multi-resource Support** – Validates files containing multiple K8s resources separated by `---`.
- 🧾 **Resource-specific Checks** – Validates required and best-practice fields for:
  - `Pod`, `Deployment`, `Service`, `Ingress`
  - `PersistentVolume (PV)`, `PersistentVolumeClaim (PVC)`
  - `StatefulSet`, `DaemonSet`, `StorageClass`
- ⚠️ **Recommended Field Warnings** – Warns when fields like `resources`, `securityContext`, `restartPolicy` are missing.
- 🎨 **Color-coded Logs** – Clear console output using ANSI colors (green = success, red = error, yellow = warning).
- 📦 **CLI Friendly** – Works directly from the command line.
- 🔀 **Supports Short Names** – e.g., `po` for Pod, `deploy` for Deployment, `svc` for Service.
- 🧱 **Extensible** – Easy to add more resources like `Job`, `CronJob`, `ConfigMap`, etc.

---

## 📦 Installation

Make sure Python 3 is installed.

```bash
git clone https://github.com/<your-username>/k8s-yaml-validator.git
cd k8s-yaml-validator
pip install pyyaml
```

---

## 🚀 Usage

```bash
python validator.py --path <file_or_directory> [--type <k8s_resource_type>]
```

### 🔹 Examples

Validate a Pod YAML file:

```bash
python validator.py --path pod.yaml --type pod
```

Validate all resources in a multi-document file:

```bash
python validator.py --path manifests.yaml --type all
```

Validate every YAML file in a folder:

```bash
python validator.py --path ./manifests --type all
```

Supported `--type` values:

- `pod`, `po`
- `deployment`, `deploy`
- `service`, `svc`
- `ingress`, `ing`
- `persistentvolume`, `pv`
- `persistentvolumeclaim`, `pvc`
- `statefulset`, `sts`
- `daemonset`, `ds`
- `storageclass`, `sc`
- `all`

---

## 📂 Output Example

```bash
✅ pod.yaml YAML validation passed - No error found.
⚠️  pod.yaml (doc #1): non-required field 'restartPolicy' is missing from Pod spec.
✅ pod.yaml (doc #1): K8s validation passed: all required fields in Pod spec are present.
```

---

## 🧱 Extending the Tool

Want to add support for more resource types like `Job`, `CronJob`, `ConfigMap`?

- Just create a new method inside the `Validator` class like `check_k8s_job()`.
- Add it to the `run()` and `all()` methods.
- Follow the same pattern used for existing checks.

---

## 👨‍💻 Contributing

Feel free to fork and submit PRs! Star the repo if you find it helpful ⭐

---

## 🪪 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Author

Built by [Preetu Sharma](https://github.com/<your-username>) – DevOps | Kubernetes | Python Enthusiast 🚀