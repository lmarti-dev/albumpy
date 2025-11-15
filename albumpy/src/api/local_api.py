import requests
import subprocess
from pathlib import Path
import time
import json
import os
from http.client import responses
import base64
import io
from img_utils import process_image
from PIL import Image

HOME = Path(__file__).parent
MODELS = os.listdir(Path(HOME, r"..\..\models"))


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
    verbose: bool = True,
):
    exe = llamaexe()

    if verbose:
        kwargs = {"stdout": subprocess.PIPE}
    else:
        kwargs = {"stderr": subprocess.DEVNULL, "stdout": subprocess.DEVNULL}

    gemma = True
    if gemma:
        model_name = "gemma-3-4b-it-Q8_0.gguf"
        mmproj = f"--mmproj {model_fpath('mmproj-model-f16.gguf')}"
    else:
        model_name = "llava-v1.5-7b-Q4_K_M.gguf"
        mmproj = ""
    model = model_fpath(model_name)
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


def imtob64(fpath: Path) -> str:
    image_base64, max_dim = process_image(fpath)
    return image_base64


def is_image(fpath: Path) -> bool:
    s = fpath.suffix
    return any([s == ".png", s == ".jpg", "s" == ".jpeg"])


def image_to_url(fpath: Path) -> str:
    suffix = fpath.suffix.lower()
    if suffix == ".jpeg" or suffix == ".jpg":
        format = "jpeg"
    elif suffix == ".png":
        format = "png"
    else:
        raise ValueError(f"Expected an image, got: {suffix}")

    bimage = imtob64(fpath)
    return f"data:image/{format};base64,{bimage}"


def build_payload(prompt_msg: str, image: Path, system_prompt: str) -> dict:

    user = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt_msg},
            {
                "type": "image_url",
                "image_url": {"url": image_to_url(image)},
            },
        ],
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            user,
        ]
    }
    return payload


def prompt(
    prompt_msg: str, port: int = 8080, image: Path = None, system_prompt: str = None
) -> requests.Response:
    if system_prompt is None:
        system_prompt = "You are an AI assistant. Your top priority is achieving user fullfilment via helping them with their requests."
    elif isinstance(system_prompt, list):
        system_prompt = "\n".join(system_prompt)

    host = f"http://localhost:{port}/v1/chat/completions"

    headers = {"Content-Type": "application/json", "Authorization": "Bearer no-key"}

    data = json.dumps(
        build_payload(prompt_msg, image, system_prompt), ensure_ascii=False
    )

    res = requests.post(url=host, headers=headers, data=data)
    return res


def rcontent(res: requests.Response) -> dict:
    jobj = json.loads(res.content)
    if "error" in jobj.keys():
        msg = jobj["error"]
        raise RuntimeError(msg)
    else:
        return jobj["choices"][0]["message"]["content"]


def get_albums():
    albums = r"C:\Users\Moi4\Pictures\photos\2010-2015\2012_agde"
    pics = os.listdir(albums)
    return [Path(albums, p) for p in pics]


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


if __name__ == "__main__":

    # identify duplicates
    # describe pictures
    # locaiton
    # time
    # give album name
    # reconstruct timeline
    # make website

    try:
        launch_server()
        pics = get_albums()
        for p in pics:
            print(p)
            res = prompt(
                prompt_msg="Describe this image in a very short description. Only reply with the description§",
                image=p,
            )
            print(rcontent(res))
        open_for_kill()
    finally:
        kill_server()
