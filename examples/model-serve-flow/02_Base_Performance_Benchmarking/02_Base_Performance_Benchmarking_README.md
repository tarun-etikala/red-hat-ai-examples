# Module 2: Performance Benchmarking

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- [Module 1: Base Accuracy Benchmarking](../01_Base_Accuracy_Benchmarking/01_Base_Accuracy_Benchmarking_README.md)
- Module 2: Base Performance Benchmarking
- [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md)
- [Module 4: Base Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md)
- [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking/05_Base_Performance_Benchmarking_README.md)
- [Module 6: Comparison](../06_Comparison/06_Comparison_README.md)
- [Module 7: Model Deployment](../07_Deployment)

## Evaluate System-level Performance of the Base Model

In addition to accuracy benchmarking, you can measure the system-level inference performance of the base model in a production-style setup. Later, after you compress the model, you use the performance baseline results from this procedure serve when you compare the base model with the compressed model.

In the following procedure, to simulate a production-like setting, you deploy the base model with vLLM, a high-throughput inference engine. You measure the inference performance of the base model under load by using the GuideLLM tool. With GuideLLM, you can generate concurrent inference traffic and collects performance metrics.

For details on system-level performance benchmarking and GuideLLM, see [Performance Benchmarking with GuideLLM](../docs/System_Level_Performance_Benchmarking.md).

### Prerequisites

- You completed the previous modules in the `model-serve-flow` project.

- The base model (`RedHatAI/Llama-3.1-8B-Instruct`) is in the `model-serve-flow/base_model/` folder.

### Procedure

- In JupyterLab, open the [Base_Performance_Benchmarking.ipynb](Base_Performance_Benchmarking.ipynb) file and follow the instructions in the notebook.

### Verification

- You successfully started the vLLM server and deployed the base model.
- The `model-serve-flow/results/` folder contains the performance metrics for the base model.

## Next step

Proceed to [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md).
