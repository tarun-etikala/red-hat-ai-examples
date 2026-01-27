# Module 5: Compressed Performance Benchmarking

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- [Module 1: Base Accuracy Benchmarking](../01_Base_Accuracy_Benchmarking/01_Base_Accuracy_Benchmarking_README.md)
- [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md)
- [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md)
- [Module 4: Base Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md)
- Module 5: Compressed Performance Benchmarking
- [Module 6: Comparison](../06_Comparison/06_Comparison_README.md)
- [Module 7: Model Deployment](../07_Deployment)

## Evaluate the System-level Performance of the Compressed Model

After you compress the base model, evaluate its system-level performance by following the same procedure that you used on Module 2 to evaluate the base model. Serve the compressed model by using vLLM and benchmark it by using GuideLLM. This consistency provides system-level metrics that you can use to compare latency, throughput, and concurrency with the same base model metrics.

For details on system-level performance benchmarking and GuideLLM, see [Performance Benchmarking with GuideLLM](../docs/System_Level_Performance_Benchmarking.md).

### Prerequisites

- You completed the previous modules in the `model-serve-flow` project.

### Procedure

- In JupyterLab, open the [Compressed_Performance_Benchmarking.ipynb](Compressed_Performance_Benchmarking.ipynb) file and follow the instructions in the notebook.

### Verification

- You successfully started the vLLM server and deployed the base model.
- The `model-serve-flow/results/` folder contains the performance metrics for the compressed model.

## Next step

Proceed to [Module 6: Comparison](../06_Comparison/06_Comparison_README.md).
