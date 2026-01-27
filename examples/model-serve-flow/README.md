## Model serve flow example

Welcome! This repository contains a self-contained example of an end-to-end workflow for the model compression, evaluation, and deployment lifecycle in a production-style setup.

Deploying full-scale large language models (LLMs) in a production environment can be costly in terms of memory, latency, and infrastructure resources. One method that alleviates these costs is model compression. Model compression enables faster inference, lower GPU usage, and scalability for real-time applications.

Model compression reduces the size and computational requirements of LLMs. However, the improvements gained from compression have the potential to impact other model capabilities, such as reasoning and knowledge. Before you deploy a compressed model, you must evaluate its accuracy and performance to validate that the benefits of compression outweigh possible costs.

## Overview of the end-to-end model serve workflow

The following diagram illustrates the overall flow of this example.

![Flow diagram](assets/model-serve-flow-diagram.png)

For this example workflow, you complete the following modules sequentially in your workbench environment:

1. **Accuracy benchmarking of the base model**

    Evaluate the accuracy of the base model before you compress it so that you can establish an accuracy benchmark.

    By creating an accuracy benchmark with the base model, you can compare it with the accuracy benchmark of the model after you compress it to evaluate how compressing the model impacts its accuracy.

2. **Performance benchmarking of the base model**

    Evaluate the performance of the base model in a production-style setup. Use the vLLM inference server to deploy the base model and make it available for system-level inference performance evaluation.

    By creating a performance benchmark with the base model, you can compare it with the performance benchmark of the model after you compress it, to evaluate how compressing the model impacts its performance.

3. **Compress the model**

    Compress the large language model by using the quantization technique. Quantization is the process of converting model parameters (weights and activations) from high-precision floating-point formats to lower-precision integer formats.

4. **Evaluate the accuracy of the compressed model**

    After you compress the model, evaluate its accuracy by using the same benchmark datasets and metrics that you used to evaluate the base model before compression. This consistency ensures a valid result when you compare the accuracy of the compressed model to the base model so that you can quantify the impact of compression.

5. **Evaluate the performance of the compressed model**

    After you compress the base model, evaluate its system-level performance by following the same procedure that you used to evaluate the base model. Serve the compressed model by using vLLM and benchmark it by using GuideLLM. This consistency provides system-level metrics that you can use to compare latency, throughput, and concurrency with the same base model metrics.

6. **Comparison**

    Compare the accuracy and performance data of the compressed and base models to provide a comprehensive view of the quantization trade-offs.

7. **Deployment**

    Deploy the compressed model on your OpenShift AI cluster or by using a vLLM inference server and verify that the deployed model can serve requests.

## About the model

This base model used in this example is `RedHatAI/Llama-3.1-8B-Instruct`.

## About the example Git repo structure

The files for each module in the workflow are organized in subfolders of this Git repository, under the `examples/model-serve-flow/` folder. Each subfolder contains a notebook, a `pyproject.toml` file for dependencies, a `utils.py` file, and a `README.md` file.

## Next step

Proceed to [Setup](./00_Setup/00_Setup_README.md).
