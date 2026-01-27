# Module 6: Comparison

## Navigation

- [Model Serving Overview](../README.md)
- [Module 0: 00_Setup](../00_Setup/00_Setup_README.md)
- [Module 1: Base Accuracy Benchmarking](../01_Base_Accuracy_Benchmarking/01_Base_Accuracy_Benchmarking_README.md)
- [Module 2: Base Performance Benchmarking](../02_Base_Performance_Benchmarking/02_Base_Performance_Benchmarking_README.md)
- [Module 3: Model Compression](../03_Model_Compression/03_Model_Compression_README.md)
- [Module 4: Base Accuracy Benchmarking](../04_Compressed_Accuracy_Benchmarking/04_Compressed_Accuracy_Benchmarking_README.md)
- [Module 5: Compressed Performance Benchmarking](../05_Compressed_Performance_Benchmarking/05_Base_Performance_Benchmarking_README.md)
- Module 6: Comparison
- [Module 7: Model Deployment](../07_Deployment)

## Compare the Accuracy and Performance Data of the Compressed and Base Models

After the model is compressed, there is some level of quantization error introduced. To provide a comprehensive view of the quantization trade-offs, compare the accuracy and performance data of the compressed and base models.

Comparing the benchmark data provides the following benefits:

- **Communicates results clearly** – Provides a single reference for model selection.

- **Evaluates trade-offs** – Shows the balance between speed, concurrency, and accuracy.

- **Supports decision-making** – Helps determine whether the compressed model is suitable for production.

For your convenience, this module includes two files that summarize the comparison of the compressed and base models.

### Prerequisites

- You completed the previous modules in the `model-serve-flow` project.

### Procedure

View a summary of the example results in [Accuracy Comparison of the Compressed and Base Models](Accuracy_Comparison.md) and [Performance Comparison of the Compressed and Base Models](Performance_Comparison.md).
