ML tests should avoid computationally intensive training.

A minimal ML smoke test should do something like this:
1. create tiny synthetic point cloud
2. run vip_hpe_core preprocessor
3. convert output to torch.Tensor
4. run one model forward pass on CPU
5. assert shape/dtype/finite output