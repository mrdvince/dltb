import logging
from multiprocessing import dummy
import os
from pathlib import Path

import hydra
import torch

from model import CLSModel, UNETModel

logger = logging.getLogger(__name__)


class ConvertModel:
    def __init__(self,cfg, ckpt_path, model_type="cls"):
        logger.info(f"Loading model from {ckpt_path}")
        if model_type == "unet":
            self.model = UNETModel.load_from_checkpoint(ckpt_path)
            self.dummy_input = torch.randn(1, 3, cfg.data.lung_mask_dim, cfg.data.lung_mask_dim)
        else:
            self.model = CLSModel.load_from_checkpoint(ckpt_path)
            self.dummy_input = torch.randn(1, 3, 224, 224)

    def to_onnx(self, save_path):
        torch.onnx.export(
            self.model,
            self.dummy_input,
            save_path,
            export_params=True,
            verbose=True,
            opset_version=10,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={
                "input": {0: "batch_size"},
                "output": {0: "batch_size"},
            },
        )

    def to_torchscript(self, save_path):
        script = self.model.to_torchscript()
        torch.jit.save(script, save_path)


@hydra.main(config_path="configs", config_name="config")
def main(cfg):
    root_dir = hydra.utils.get_original_cwd()
    ckpt_path = os.path.join(root_dir, cfg.ckpt_path)
    save_path = os.path.join(root_dir, cfg.data.exports_dir)

    Path(save_path).mkdir(parents=True, exist_ok=True)

    cm = ConvertModel(cfg, ckpt_path=ckpt_path, model_type=cfg.model.type)
    cm.to_onnx(os.path.join(save_path, "model_best_checkpoint.onnx"))
    cm.to_torchscript(os.path.join(save_path, "model_best_checkpoint.pt"))


if __name__ == "__main__":
    main()
