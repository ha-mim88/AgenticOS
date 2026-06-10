import json
import time
import requests

base = "http://127.0.0.1:5000/api"

resp = requests.post(
    f"{base}/vibe/generate",
    json={
        "thoughts": "Summarize customer support complaints and produce a markdown action report",
        "output_spec": "Create a markdown report file with summary, issues, recommendations",
        "max_depth": 10,
        "max_iterations_per_depth": 500,
    },
    timeout=120,
)
print("generate", resp.status_code)
d = resp.json()
print("has mermaid", bool(d.get("mermaid")), "steps", len(d.get("steps", [])))
assert resp.status_code == 200
assert d.get("mermaid")
assert d.get("steps")

save = requests.post(
    f"{base}/vibe/tasks",
    json={
        "title": d.get("title", "Support report automation"),
        "thoughts": "Summarize customer support complaints and produce a markdown action report",
        "output_spec": "Create a markdown report file with summary, issues, recommendations",
        "generated_mermaid": d.get("mermaid", ""),
        "generated_plan": d,
        "max_depth": 10,
        "max_iterations_per_depth": 500,
    },
    timeout=30,
)
print("save", save.status_code)
print(save.text[:200])
assert save.status_code == 201
saved = save.json()

tree = requests.get(f"{base}/vibe/tree", timeout=30).json()
print("tree count", len(tree))
assert len(tree) >= 1

execute = requests.post(
    f"{base}/vibe/tasks/{saved['id']}/execute",
    json={
        "thoughts": "Customer complaints: login broken, slow checkout, refund delay",
        "output_spec": "Create markdown report",
    },
    timeout=30,
)
print("execute", execute.status_code)
print(execute.text[:200])
assert execute.status_code == 202
execution = execute.json()
guid = execution["execution_guid"]

final_info = None
for i in range(30):
    time.sleep(2)
    info = requests.get(f"{base}/vibe/executions/{guid}", timeout=30).json()
    print("poll", i, info["status"], info.get("token_usage", 0))
    final_info = info
    if info["status"] != "running":
        break

assert final_info is not None
assert final_info["status"] in {"success", "failed"}

logs = requests.get(f"{base}/vibe/executions/{guid}/logs", timeout=30).json()
print("logs", len(logs))
assert len(logs) >= 1

file_tree = requests.get(f"{base}/vibe/executions/{guid}/tree", timeout=30).json()
print("root", file_tree.get("name"), "children", len(file_tree.get("children", [])))
assert file_tree.get("type") == "folder"
assert len(file_tree.get("children", [])) >= 1

print("SUCCESS: Vibe Sandbox flow exercised end-to-end")

