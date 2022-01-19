from abc import abstractmethod

import numpy as np
import torch

from base.base_config import Config


class BaseTrainer:
    def __init__(self, model, optimizer, criterion, metrics, config: Config):
        self.config = config
        self.verbosity = config.verbosity
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.metrics = metrics

        self.epochs = config.epochs
        self.save_period = config.save_period
        self.monitor_mode = config.monitor[0]
        self.monitor_metric = config.monitor[1]
        assert self.monitor_mode in [
            "min",
            "max",
        ], "monitor_mode should be either 'min' or 'max'"
        self.monitor_best = np.inf if self.monitor_mode == "min" else -np.inf
        self.early_stop = config.early_stop
        self.start_epoch = 1
        self.checkpoint_dir = config.save_dir
        # visualization
        # TODO: add wandb logging

        @abstractmethod
        def _train(self, epoch):
            raise NotImplementedError

        def train(self):
            not_improved = 0
            for epoch in range(self.start_epoch, self.epochs + 1):
                result = self._train(epoch)

                # log dict
                log = {"epoch": epoch}
                log.update(result)

                best = False
                # default -> self.monitor_metric = 'val_loss'
                if self.monitor_metric in result:
                    current = result[self.monitor_metric]
                    improved = (
                        self.monitor_mode == "min" and current < self.monitor_best
                    ) or (self.monitor_mode == "max" and current > self.monitor_best)
                    if improved:
                        self.monitor_best = current
                        not_improved = 0
                        best = True
                    else:
                        not_improved += 1

                    if self.early_stop is not None:
                        if not_improved > self.early_stop:
                            print("early stopping at epoch {}".format(epoch))
                            break

                if epoch % self.save_period == 0:
                    self._save_checkpoint(self, epoch, is_best=best)

        def _save_checkpoint(self, epoch, is_best=False):
            arch = type(self.model).__name__
            state = {
                "arch": arch,
                "epoch": epoch,
                "cls_to_idx": self.data_loader.dataset.class_to_idx,
                "state_dict": self.model.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "monitor_best": self.monitor_best,
                "config": self.config,
            }
            filename = str(self.checkpoint_dir / "checkpoint-epoch{}.pth".format(epoch))
            torch.save(state, filename)
            print("Saving checkpoint: {} ...".format(filename))
            if is_best:
                best_filename = str(self.checkpoint_dir / "model_best.pth")
                torch.save(state, best_filename)
                print("Saving current best: {} ...".format(best_filename))