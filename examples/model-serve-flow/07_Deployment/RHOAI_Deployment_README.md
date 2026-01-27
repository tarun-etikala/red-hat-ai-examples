# Deploying the Compressed Large Language Model on Red Hat OpenShift AI

In the previous modules in the model serving flow, you compressed a LLaMA 3.1 8B INT8 model, validated its accuracy, and benchmarked its performance.

The following procedure describes how to deploy the compressed model on your OpenShift AI cluster, retrieve the necessary endpoints and token, and verify that the deployed model can serve requests.

**NOTE:** Alternately, you can deploy the compressed model on the vLLM inference server as described in [Deploying the Compressed Model by Using a vLLM Server](VLLM_Deployment_README.md).

## Prerequisites

* You completed the previous modules in the `model-serve-flow` project.
* You stopped any running workbench that uses the PVC where the compressed model is stored. A PVC cannot be shared between an active workbench and a model deployment.
* You have installed the `curl` utility or Python and the OpenAPI SDK.

## Procedure

1. In the OpenShift AI dashboard, open the project where your model is stored.
2. Navigate to the `Deployments tab` and then click `Deploy Model`.

   ![Shown here](../assets/01.png)

3. Fill out the **Model Details** section:

   a. Set **Model location** to `Cluster Storage`.

   b. In **Model path**, specify the path to the compressed model stored in the PVC. For example: `red-hat-ai-examples/examples/model-serve-flow/Llama_3.1_8B_Instruct_int8_dynamic`.

   c. For **Model type**, select `Generative AI model (Examople LLM)`.

   d. Click **Next**.

   ![Shown here](../assets/02.png)

4. Fill out the **Model Deployment** section:

    a. Provide a value for **Model deployment name**, for example: `llama-3.1-8b-int8`.

    b. Set `Hardware Profile` to `Nvidia GPU Accelerator`.

    c. Configure the following compute resources:

    * Expand the **Custom resource requests and limits** dropdown.

    * Set CPU and memory requests and limits based on the model size and expected workload for this example:
         CPU: Request = 2 Cores, Limit = 2 Cores
         Memory: Request = 4 GiB, Limit = 4 GiB

    * Specify the number of GPUs to allocate for this example:
         Nvidia GPU: Request =1, Limit =1

    * Set the `Serving runtime` to `vLLM NVIDIA GPU ServingRuntime KServe`.

    e. Leave the number of replicas as 1.

    f. Click **Next**.

    ![Shown here](../assets/03.png)

5. Fill out the **Advanced Settings** section:

    a. For **Model access**, enable `Make model deployment available through an external route`.

    b. For **Token authentication**, enable `Require token authentication`.

    c. For **Configuration parameters**, enable `Add custom runtime environment variables`.

    d. Add the following environment variable:

    ```text
    Name: `VLLM_LOGGING_LEVEL`
    Value: `DEBUG`
    ```

    d. For **Deployment strategy**, select `Rolling update`.

    e. Click **Next** and then review the deployment details.

    ![Shown here](../assets/04.png)

6. Click **Deploy Model**.

7. Navigate to the **Deployments** tab.

    The model deployment (for example, `llama-31-8b-int8`) initially shows a status of `Starting`.

8. Wait until the status changes to `Started`, indicating that the model is ready to serve requests.

9. Obtain the endpoints and token to interact with the model:

    a. In the **Deployments** tab, locate your model deployment (for example, `llama-31-8b-int8`).

    b. Click on the **dropdown** for the deployment to expand details.

    c. Copy the token.

    d. Click **internal and external endpoints** to get the endpoints. Use the `internal endpoint` when accessing the model from within the cluster and the `external enpoint` from outside the cluster.

    ![Retrieve token](../assets/05.png)

    ![Retrieve endpoints](../assets/06.png)

## Verification

If the deployment status is **Started**, you can verify that the model is serving requests by using a `curl` command or the OpenAI Python SDK.

### Run a curl request

1. Open a new terminal window and log in to your OpenShift cluster.

    In the upper-right corner of the OpenShift web console, click your user name and select *Copy login command*. After you have logged in, click *Display token*. Copy the *Log in with this token* command and paste it in the {openshift-cli}.

    ```text
    oc login --token=__<token>__ --server=__<openshift_cluster_url>__
    ```

2. Run the following command:

    ```text
    curl -X POST "<external_endpoint>/v1/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer "<your_token>" \
      -d '{
        "model": "llama-31-8b-int8",
        "prompt": "What is photosynthesis?",
        "max_tokens": 128,
        "temperature": 0.5
      }'
    ```

A valid response, such as the following example, confirms that the model is deployed and serving requests.

```bash
{
  "id": "1",
  "object": "text_completion",
  "created": 1767956024,
  "model": "llama-31-8b-int8",
  "choices": [
    {
      "index": 0,
      "text": " Photosynthesis is the process by which plants, algae, and some bacteria convert light energy from the sun into chemical energy in the form of glucose. This process occurs in specialized organelles called chloroplasts, which contain the pigment chlorophyll that absorbs light energy.\nPhotosynthesis is essential for life on Earth as it provides the energy and organic compounds needed to support the food chain. Without photosynthesis, plants would not be able to produce the glucose they need to grow and thrive, and animals would not have a source of food.\nThe overall equation for photosynthesis is:\n6 CO2 + 6 H2O + light energy →",
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null,
      "token_ids": null,
      "prompt_logprobs": null,
      "prompt_token_ids": null
    }
  ],
  {
  "service_tier": null,
  "system_fingerprint": null,
  "usage": {
    "prompt_tokens": 6,
    "total_tokens": 134,
    "completion_tokens": 128,
    "prompt_tokens_details": null
  },
  "kv_transfer_params": null
}
```

### Use the OpenAI SDK

To use the OpenAI Python SDK to test the model deployment, run the following code:

```python
!pip install openai

from openai import OpenAI

api_key = "<your_token>"
internal_url = "<your_internal_endpoint>/v1"
external_url = "<external_endpoint>/v1"

# Use external_url if accessing the model from outside the cluster
# Use internal_url if you are accessing the model from within the same OpenShift cluster
client = OpenAI(
    base_url=external_url,
    api_key=api_key
)

response = client.completions.create(
    model="llama-31-8b-int8",
    prompt="What is photosynthesis?",
    max_tokens=128,
    temperature=0.5
)

print(response.choices[0].text)
```

## Debugging Model Deployment in the OpenShift Console

To debug issues that you encounter when you deploy the model, follow these steps to access the logs for the deployed model:

1. Open the Openshift Console.

2. Click **Workloads**, and then select **Pods**.

   ![Shown here](../assets/07.png)

3. Search for your project by name, and then click your project.

   ![Shown here](../assets/08.png)

4. Click **Pods** to view a list of all pods associated with your project.

5. Locate the deployment pod by using the name specified during model deployment (for example, `llama-31-8b-int8`).

   ![Shown here](../assets/09.png)

6. Click the pod name and navigate to the **Logs** tab to monitor its logs.

  ![Shown here](../assets/10.png)
