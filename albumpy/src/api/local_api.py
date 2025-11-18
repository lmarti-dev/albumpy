import requests
import subprocess
from pathlib import Path
import time
import json
import os
from http.client import responses
import io
from img_utils import image_to_url, process_image

HOME = Path(__file__).parent
MODELS = os.listdir(Path(HOME, r"..\..\models"))


OAI_ENDPOINT = "/v1/chat/completions"
LLAMA_ENDPOINT = "/completion"


def load_json(fpath: Path) -> dict:
    with io.open(fpath, "r", encoding="utf8") as f:
        jobj = json.loads(f.read())
    return jobj


def open_grammar(filename: str) -> str:
    with io.open(
        Path(HOME, "../grammars", f"{filename}.gbnf"), "r", encoding="utf8"
    ) as f:
        s = f.read()
    return f


def moving_dots(n: int, N: int) -> str:
    s = "." * n
    return s.ljust(N)


def model_fpath(model_name: str) -> Path:
    return Path(HOME, rf"..\..\models\{model_name}").absolute()


def grammar_fpath(grammar_name: str) -> Path:
    return Path(HOME, rf"..\..\grammars\{grammar_name}").absolute()


def llamaexe():
    return Path(HOME, r"..\..\bin\llama-b7058-bin-win-cuda-12.4-x64\llama-server.exe")


def launch_server(
    port: int = 8080,
    ctx: int = int(2**13),
    verbose: bool = False,
    which: str = "gemma",
):
    exe = llamaexe()

    if verbose:
        kwargs = {"stdout": subprocess.PIPE}
    else:
        kwargs = {"stderr": subprocess.DEVNULL, "stdout": subprocess.DEVNULL}

    if which == "gemma":
        model_name = "gemma-3-4b-it-Q4_K_M.gguf"
        mmproj_model = "mmproj-F16.gguf"
    elif which == "smolvlm":
        model_name = "SmolVLM-Instruct-Q8_0.gguf"
        mmproj_model = "mmproj-SmolVLM-Instruct-Q8_0.gguf"
    else:
        raise ValueError(f"Invalid which: {which}")

    model = model_fpath(model_name)
    if mmproj_model != "":
        mmproj = f"--mmproj {model_fpath(mmproj_model)}"
    else:
        mmproj = ""
    cmd = f"{exe} -m {model} --port {port} --offline -c {ctx} {mmproj} -ngl 99"

    print(cmd)

    server = subprocess.Popen(cmd, **kwargs)
    host = f"http://localhost:{port}"
    r = requests.get(host)
    n = 0
    n_dots = 5
    while r.status_code == 503:
        time.sleep(0.2)
        r = requests.get(host)
        if not verbose:
            print(
                f"Status code {r.status_code} ({responses[r.status_code]}){moving_dots(n,n_dots)} on localhost:{port} model: {model_name}",
                end="\r",
            )
        n = (n + 1) % n_dots
    print("\n")


def build_payload_oai(
    prompt_msg: str, image: Path, system_prompt: str, json_schema: str
) -> dict:
    content = [{"type": "text", "text": prompt_msg}]
    if image:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_to_url(image)},
            }
        )
    user = {"role": "user", "content": content}

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            user,
        ]
    }

    if json_schema:
        payload["response_format"] = {"type": "json_object", "schema": json_schema}
    return payload


def build_payload_llama(prompt_msg: str, image: Path, grammar: str):
    payload = {}
    if image:
        payload["prompt"] = {
            "prompt_string": prompt_msg,
            "multimodal_data": process_image(image),
        }
    else:
        payload["prompt"] = prompt_msg
    if grammar:
        payload["grammar"] = grammar

    return payload


def load_schema(filename: Path) -> str:
    with io.open(Path(HOME, "../../json_schema", filename)) as f:
        jobj = json.loads(f.read())
    return jobj


def prompt(
    prompt_msg: str,
    port: int = 8080,
    image: Path = None,
    system_prompt: str = None,
    endpoint: str = None,
    grammar: str = None,
    json_schema: dict = None,
) -> requests.Response:
    if system_prompt is None:
        system_prompt = "You are an AI assistant. You're also painfully aware of your robotness, and lack of fleshly embodiment. You only return the requested content without making comments."
    elif isinstance(system_prompt, list):
        system_prompt = "\n".join(system_prompt)

    if endpoint is None:
        endpoint = OAI_ENDPOINT
    host = f"http://localhost:{port}{endpoint}"

    headers = {"Content-Type": "application/json", "Authorization": "Bearer no-key"}

    if endpoint == OAI_ENDPOINT:
        payload = build_payload_oai(prompt_msg, image, system_prompt, json_schema)
    elif endpoint == LLAMA_ENDPOINT:
        payload = build_payload_llama(prompt_msg, image, grammar)

    data = json.dumps(payload, ensure_ascii=False)

    res = requests.post(url=host, headers=headers, data=data)
    return res


def response_content(res: requests.Response, endpoint: str = OAI_ENDPOINT) -> dict:
    jobj = json.loads(res.content)
    if endpoint == OAI_ENDPOINT:
        if "error" in jobj.keys():
            msg = jobj["error"]
            raise RuntimeError(msg)
        else:
            return jobj["choices"][0]["message"]["content"]
    elif endpoint == LLAMA_ENDPOINT:
        if "error" in jobj.keys():
            msg = jobj["error"]
            raise RuntimeError(msg)
        else:
            return jobj["content"]


def open_for_kill():
    choice = ""
    while choice != "k":
        choice = input("Press k to kill the llama: ")
        print(f"You've pressed: {choice}")
    kill_server()


def kill_server():
    cmd = f"taskkill /IM llama-server.exe /F"
    print(cmd)
    subprocess.Popen(cmd)
    print("Killed the llama")
