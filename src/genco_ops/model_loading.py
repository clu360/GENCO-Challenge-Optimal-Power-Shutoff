"""Production GENCO task construction without research-pipeline imports."""

import importlib


def native_args(config):
    from gridfm_graphkit.io.param_handler import NestedNamespace
    return NestedNamespace(**{
        "task": {"task_name": "PowerFlow"},
        "data": {"baseMVA": 100., "mask_value": 0., "networks": ["stage_m_pf_pilot"]},
        "model": {"type": "GNS_heterogeneous", "attention_head": 8, "edge_dim": 10,
                  "hidden_size": 48, "input_bus_dim": 15, "input_gen_dim": 6,
                  "output_bus_dim": 2, "output_gen_dim": 1, "num_layers": 12, "dropout": 0.},
        "optimizer": {"learning_rate": config["learning_rate"], "beta1": .9, "beta2": .999,
                      "lr_decay": .7, "lr_patience": 5},
        "training": {"batch_size": 1, "epochs": config["epochs"],
                     "losses": ["LayeredWeightedPhysics", "MaskedBusMSE"],
                     "loss_weights": [.1, .9], "loss_args": [{"base_weight": .5}, {}]},
        "verbose": False,
    })


def build_native_task(request, contract, checkpoint):
    """Shared official task construction for training, reload and evaluation."""
    import torch
    from gridfm_graphkit.datasets.normalizers import HeteroDataMVANormalizer
    from gridfm_graphkit.io.param_handler import NestedNamespace
    args = native_args(request['recipe'])
    args.task.task_name = contract['task']
    args.training.batch_size = request['recipe']['batch_size']
    args.training.losses = contract['losses']
    args.training.loss_weights = contract['loss_weights']
    args.training.loss_args = [NestedNamespace(**value) for value in contract['loss_args']]
    task_type = getattr(importlib.import_module(contract['task_module']), contract['task_class'])
    stats = next(iter(torch.load(request['normalizer'], map_location='cpu', weights_only=True).values()))
    normalizer = HeteroDataMVANormalizer(args)
    normalizer.fit_from_dict(stats)
    task = task_type(args, [normalizer])
    weights = torch.load(checkpoint, map_location='cpu', weights_only=True)
    task.model.load_state_dict({key.removeprefix('model.'): value for key, value in weights.items()}, strict=True)
    return task, stats
