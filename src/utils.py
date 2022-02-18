import logging
import os
import shutil
from glob import glob
from pathlib import Path

import opendatasets as od
import pandas as pd
from PIL import Image, ImageChops
from tqdm.auto import tqdm
import torch


def get_pandas_entry(id, path="data/train.csv"):
    df = pd.read_csv(path)
    classes = ["negative", "positive"]
    label = int(df[df["ID"] == id]["LABEL"])
    return classes[label], label


def copy_images_to_folder(project_root, data_dir):
    project_root = Path(project_root)
    image_list = [path for path in Path(data_dir).rglob("*.png")]
    for idx, image in enumerate(image_list):
        image_name = image.name
        _, label = get_pandas_entry(image_name.split(".")[0])
        image_path = image.as_posix()
        if label == 0:
            # copy image to negative folder
            negative_path = Path(project_root / "data/proc_tb/negative")
            logging.info(f"Copying {image_path} to {negative_path}")
            negative_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(image_path, negative_path / image_name)
        if label == 1:
            # copy image to positive folder
            positive_path = Path(project_root / "data/proc_tb/positive")
            logging.info(positive_path)
            positive_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(image_path, positive_path / image_name)
    return "done"


def verify_images_labels(name):
    return get_pandas_entry(name)


def download(dataset_url, data_dir):
    od.download(dataset_url, data_dir)


def copy_cxr_merge_masks(raw_image_dir, cxr_dir, mask_dir):
    image_paths = glob(os.path.join(raw_image_dir, "*.png"))
    # fmt: off
    images_with_masks_paths = [
        (image_path,os.path.join("/".join(image_path.split("/")[:-2]),"ManualMask","leftMask", os.path.basename(image_path)),
         os.path.join("/".join(image_path.split("/")[:-2]),"ManualMask","rightMask",os.path.basename(image_path))) for image_path in image_paths
        ]
    # fmt: on
    mask_path = Path(mask_dir)
    mask_path.mkdir(exist_ok=True, parents=True)

    cxr_path = Path(cxr_dir)
    cxr_path.mkdir(exist_ok=True, parents=True)

    for cxr, left, right in tqdm(images_with_masks_paths):
        left = Image.open(left).convert("L")
        right = Image.open(right).convert("L")
        seg_img = ImageChops.add(left, right)
        filename = Path(cxr).name
        shutil.copy(cxr, cxr_path / filename)
        seg_img.save(mask_path / filename)


def get_data(
    cxr_dir="data/proc_seg/cxr_pngs",
    mask_dir="data/proc_seg/mask_pngs",
    data_dir="data",
):
    download(
        "https://www.kaggle.com/kmader/pulmonary-chest-xray-abnormalities",
        data_dir=data_dir,
    )
    copy_cxr_merge_masks(
        raw_image_dir="data/pulmonary-chest-xray-abnormalities/Montgomery/MontgomerySet/CXR_png",
        cxr_dir=cxr_dir,
        mask_dir=mask_dir,
    )


if __name__ == "__main__":
    copy_images_to_folder(Path.cwd(), "data/tb_data/train")
    get_data()
