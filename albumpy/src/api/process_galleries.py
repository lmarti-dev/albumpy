from local_api import (
    prompt,
    response_content,
    launch_server,
    open_for_kill,
    kill_server,
    load_schema,
)
import time
from pathlib import Path
import io
import json
import os

HOME = Path(__file__).parent


def get_photos(albums):
    pics = os.listdir(albums)
    return [Path(albums, p) for p in pics]


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


def save_json(jobj: dict, fpath: Path) -> None:
    with io.open(fpath, "w+", encoding="utf8") as f:
        f.write(json.dumps(jobj, ensure_ascii=False))


def build_pic_dict(p: Path) -> dict:
    description = describe_picture(p)
    location = locate_picture(p)
    grade = rate_picture(p)
    date = date_picture(p)
    return {
        "description": description,
        "location": location,
        "grade": grade,
        "date": date,
    }


if __name__ == "__main__":

    # identify duplicates
    # describe pictures
    # locaiton
    # time
    # give album name
    # reconstruct timeline
    # make website

    d = {}
    try:
        launch_server()
        pics = get_photos()
        for p in pics:
            tic = time.time()
            pposix = p.as_posix()
            print(pposix)
            d[pposix] = build_pic_dict(p)
            toc = time.time()
            print(f"Processing {p} took {toc-tic} sec.")
            save_json(d, Path(HOME, "test.json"))
        open_for_kill()

    finally:
        kill_server()
