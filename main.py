import json
import os
import threading

from langsmith import Client, traceable
from langsmith.run_helpers import get_current_run_tree

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "CHANGE_ME"
os.environ["LANGCHAIN_PROJECT"] = "CHANGE_ME"


def hide_inputs(inputs: dict) -> dict:
    result = inputs.copy()
    result["seen_by_hide_inputs"] = True
    return result


@traceable
def run_worker_task(inputs: dict) -> str:
    return f"Worker Result with {next(iter(inputs))}"


def worker():
    langsmith_headers = json.loads(os.environ.get("LANGSMITH_HEADERS"))
    langsmith_client = Client(hide_inputs=hide_inputs)
    inputs = {
        "super_secret_key": "iNeedToBeMasked",
    }
    run_worker_task(
        inputs,
        langsmith_extra={
            "client": langsmith_client,
            # Uncomment me to use the main task as a parent, but hide_inputs will stop working
            # "parent": langsmith_headers,
        },
    )


@traceable
def run_main_task():
    if run_tree := get_current_run_tree():
        os.environ["LANGSMITH_HEADERS"] = json.dumps(run_tree.to_headers())

    thread = threading.Thread(target=worker, name="WorkerThread")
    thread.start()
    thread.join()
    return run_tree.to_headers()


def main():
    langsmith_client = Client(hide_inputs=hide_inputs)
    run_main_task(langsmith_extra={"client": langsmith_client})


if __name__ == "__main__":
    main()
