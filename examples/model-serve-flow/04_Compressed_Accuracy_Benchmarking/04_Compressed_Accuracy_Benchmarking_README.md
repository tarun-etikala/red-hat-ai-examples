# Module 4: Compressed Accuracy Benchmarking

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- [Module 1: Base Accuracy Benchmarking](../01_Base_Accuracy_Benchmarking/01_Base_Accuracy_Benchmarking_README.md)
- [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md)
- [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md)
- Module 4: Base Accuracy Benchmarking
- [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking/05_Base_Performance_Benchmarking_README.md)
- [Module 6: Comparison](../06_Comparison/06_Comparison_README.md)
- [Module 7: Model Deployment](../07_Deployment)

## Evaluate the Accuracy of the Compressed Model

After you compress the model, use the LMEval tool (`lm_eval`) to run accuracy benchmarking on it. Evaluate the compressed model by using the same benchmark datasets and metrics that you used to evaluate the base model in Module 1. This consistency ensures a valid result when you compare the accuracy of the models so that you can quantify the impact of quantization.

For details on evaluating LLMs for accuracy, see [AcEvaluate the Accuracy of the Base and Compressed Models](../docs/Accuracy_Evaluation.md).

### Prerequisites

- You completed the previous modules in the `model-serve-flow` project.

### Procedure

- In JupyterLab, open the [Compressed_Accuracy_Benchmarking.ipynb](Compressed_Accuracy_Benchmarking.ipynb) file and follow the instructions in the notebook.

### Verification

The `model-serve-flow/results/` folder contains the results for the compressed model accuracy benchmarking procedure.

## Next step

Proceed to [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking_README.md).
