from pygguf import (
    prompt,
    response_content,
    launch_server,
    open_for_kill,
    kill_server,
    load_schema,
    load_json,
    is_image,
)
import time
from pathlib import Path
import io
import json
import os

import re
import uuid

HOME = Path(__file__).parent
DATA_PATH = Path(HOME, "../../data")


def get_photos(albums):
    pics = os.listdir(albums)
    return [Path(albums, p) for p in pics if is_image(Path(p))]


def describe_picture(p: Path) -> str:
    res = prompt(
        prompt_msg="Describe this image in a 100 words. Only reply with the description",
        image=p,
    )
    return response_content(res)


def locate_picture(p: Path) -> str:
    res = prompt(
        prompt_msg=f"Try to guess the location of the picture and only output the result in the form City, Country. Or only Country if you can't guess the city. Use the filename of the picture for more clues: {p}",
        image=p,
    )
    return response_content(res)


def date_picture(p: Path) -> str:
    res = prompt(
        prompt_msg=f"Try to guess the date of the picture and output the result in the form dd/mm/yyyy. Only return the date in format dd/mm/yyyy and nothing else. Use the filename of the picture for more clues: {p}",
        image=p,
    )
    return response_content(res)


def rate_picture(p: Path):
    res = prompt(
        prompt_msg="Rate the aesthetics image 1 to 100 with 100 being the best. Only output the number and nothing else",
        image=p,
        json_schema=load_schema("grade.json"),
    )
    return response_content(res)


def caption_picture(p: Path):
    res = prompt(
        prompt_msg="Make a nice, fun, playful one-sentence caption for this picture. Only output the caption and nothing else",
        image=p,
    )
    return response_content(res)


def summarise_gallery(d: dict) -> str:
    del d["summary"]
    res = prompt(
        prompt_msg=f"Like an old friend being shown photos, muse about -- in a fun way and in three or four paragraphs -- the general vibe of events described by the json {d}. Address the author in the second person, with familiarity, playful banter. No introduction, just jump into it.",
    )
    text = response_content(res)
    pars = re.split(r"\n{2,}", text)
    return pars


def name_gallery(d: dict) -> str:
    res = prompt(
        prompt_msg=f"Find a fun and good 40 char title for this picture gallery given its description: {d}. Only return the title and nothing else",
    )
    return response_content(res)


def save_json(jobj: dict, fpath: Path) -> None:
    with io.open(fpath, "w+", encoding="utf8") as f:
        f.write(json.dumps(jobj, ensure_ascii=False))


def build_pic_dict(p: Path) -> dict:
    description = describe_picture(p)
    location = locate_picture(p)
    grade = rate_picture(p)
    date = date_picture(p)
    caption = caption_picture(p)
    return {
        "description": description,
        "location": location,
        "grade": grade,
        "date": date,
        "caption": caption,
        "path": p.as_posix(),
    }


def build_json_for_gallery(dirname: Path, filename_out: str = None) -> None:

    launch_server()
    d = {"photos": []}
    if filename_out is None:
        filename_out = uuid.uuid4()
    pics = get_photos(dirname)
    n_pics = len(pics)
    for ind, p in enumerate(pics):
        tic = time.time()
        pposix = p.as_posix()
        print(f"{ind:0>4}/{n_pics:0>4} - {pposix}")
        pd = build_pic_dict(p)
        d["photos"].append(pd)
        toc = time.time()
        print(f"Processing {p} took {toc-tic} sec.")
        save_json(d, Path(DATA_PATH, f"{filename_out}.json"))
    title = name_gallery(d)
    summary = summarise_gallery(d)
    d["title"] = title
    d["summary"] = summary
    save_json(d, Path(DATA_PATH, f"{filename_out}.json"))
    open_for_kill()


def resummarize(fpath: Path) -> str:
    jobj = load_json(fpath)
    summary = summarise_gallery(jobj)
    print(summary)


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
        new_summary = resummarize(
            r"C:\Users\Moi4\Desktop\code\llm\albumpy\albumpy\data\3e5d9dcf-1723-482b-9a1e-0bcd85ed91d5.json"
        )
        fire.Fire(build_json_for_gallery)
    finally:
        kill_server()
