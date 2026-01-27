# Module 3: Model Compression

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- [Module 1: Base Accuracy Benchmarking](../01_Base_Accuracy_Benchmarking/01_Base_Accuracy_Benchmarking_README.md)
- [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md)
- Module 3: Model Compression
- [Module 4: Base Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md)
- [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking/05_Base_Performance_Benchmarking_README.md)
- [Module 6: Comparison](../06_Comparison/06_Comparison_README.md)
- [Module 7: Model Deployment](../07_Deployment)

## Compress the Base Model

Compress a Large Language Model (LLM) to reduce its size and computational cost while preserving as much accuracy as possible, enabling faster and more efficient deployment.

In this example, you use the LLM Compressor tool to apply the quantization compression technique on the base model. Quantization converts model parameters (weights and activations) from high-precision floating-point formats (for example, FP16 or BF16) to lower-precision integer formats (for example, INT8).

Quantization provides the following benefits:

- *Reduces memory usage*: Lower precision weights occupy less GPU memory, allowing larger batch sizes and longer key-value (KV) caches, which improves overall system throughput.

- *Speeds up computation*: Low-precision matrix multiplications (INT8/FP8) are inherently faster on modern GPU architectures than high-precision operations, significantly reducing inference time.

- *Enables deployment on resource-constrained environments*: Quantization makes large language models feasible for real-time applications and devices with limited (Video Random Access Memory (VRAM).

The quantization scheme for this example is INT8 W8A8 (8-bit weights and 8-bit activations), specifically employing dynamic quantization of activations.

For more information about compression and quantization, see [Compress a Large Language Model by using LLM Compressor](../docs/Compression.md).

### Prerequisites

- You completed the previous modules in the `model-serve-flow` project.

- The base model (`RedHatAI/Llama-3.1-8B-Instruct`) is in the `model-serve-flow/base_model/` folder.

### Procedure

- In JupyterLab, open the [Model_Compression.ipynb](Model_Compression.ipynb) file and follow the instructions in the notebook.

### Verification

- A compressed model named `RedHatAI-Llama-3.1-8B-Instruct-int8-dynamic` is in the `model-serve-flow/compressed_model` folder.
- When you compare the size of the compressed model to the size of the base model, the compressed model is almost half the size of the base model.

## Next step

Proceed to [Module 4: Compressed Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md).
