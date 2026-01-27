# Module 1: Base Accuracy Benchmarking

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- Module 1: Base Accuracy Benchmarking
- [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md)
- [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md)
- [Module 4: Base Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md)
- [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking/05_Base_Performance_Benchmarking_README.md)
- [Module 6: Comparison](../06_Comparison/06_Comparison_README.md)
- [Module 7: Model Deployment](../07_Deployment)

## Evaluate the Accuracy of the Base Model

Before you compress the base model, use the LMEval tool to run accuracy benchmarking on it. You need to obtain an accuracy benchmark for the base model so that you can compare it with the accuracy of the model after you compress it.

The process of compressing a model can introduce rounding errors that can degrade the accuracy of a model. With accuracy benchmarking, you can confirm that the speed improvements gained from compression do not come at a significant cost to model capabilities, such as reasoning and knowledge.

For details on evaluating LLMs for accuracy, see [Evaluate the Accuracy of the Base and Compressed Models](../docs/Accuracy_Evaluation.md).

### Prerequisites

- You completed the [Setup](../00_Setup/00_Setup_README.md) module.

### Procedure

- In JupyterLab, open the [Base_Accuracy_Benchmarking.ipynb](Base_Accuracy_Benchmarking.ipynb) file and follow the instructions in the notebook.

### Verification

- The `model-serve-flow/base_model/` folder contains the base model: `RedHatAI/Llama-3.1-8B-Instruct`.
- The `model-serve-flow/results/` folder contains the results of the accuracy benchmarking for the base model.

## Next step

Proceed to [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md).
