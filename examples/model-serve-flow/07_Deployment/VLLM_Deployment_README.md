# Deploying the Compressed Model by Using a vLLM Server

You can deploy a compressed model by using a vLLM inference server.

**NOTE:** Alternately, you can deploy the compressed model on a Red Hat OpenShift AI cluster as described in [Deploying the Compressed Large Language Model on Red Hat OpenShift AI](07_Deployment/RHOAI_Deployment_README.md).

## Prerequisites

* You completed the previous modules in the `model-serve-flow` project.
* You have installed the `curl` utility or Python and the OpenAPI SDK.

## Procedure

1. Start the vLLM server and point it to your compressed model:

    ```bash
    vllm serve /path/to/model \
     --host 0.0.0.0 \
      --port 8000 \
      --api-key <"confgure your secret token"> \
      --tensor-parallel-size <num of GUPs available per node> \
      --pipeline-parallel-size <total number of available nodes> \
      --max-model-len 8192 \
      --enable-prefix-caching \
      --max-num-batched-tokens 8192 \
      --max-num-seqs 1024 \
      --gpu-memory-utilization 0.9 \
      --quantization compressed-tensors \
      --disable-log-stats \
    ```

2. Wait for the server to start.

3. To verify that the server is running, run the following command to check whether it is listening on port 8000:

    ```bash
    curl -v http://localhost:8000/health
    ```

    A successful response of `200 OK` confirms that the server is live.

4. Run the following code to test the server:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",  # Use local server endpoint
    api_key=<your secret token>
)
response = client.chat.completions.create(
    model= "path to the model", #e.g. ../Llama_3.1_8B_Instruct_int8_dynamic
    messages=[{"role": "user", "content": "What is photosynthesis?"}],
)

print(response.choices[0].message.content)
```
