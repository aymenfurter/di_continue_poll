import os
import json
import re
import base64
import argparse
from azure.core.polling import LROPoller
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, ContentFormat, AnalyzeResult
from azure.core.pipeline import PipelineResponse
from azure.core.polling.base_polling import LROBasePolling

def deserialize_analyze_result(pipeline_response: PipelineResponse):
    camel_to_snake = lambda name: re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    response_json = json.loads(pipeline_response.http_response.text())["analyzeResult"]
    return AnalyzeResult(**{camel_to_snake(k): v for k, v in response_json.items()})

def analyze_documents():
    endpoint = os.getenv("AZURE_ENDPOINT", "https://default.cognitiveservices.azure.com/")
    key = os.getenv("AZURE_KEY", "default_key")
    url = "https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/documentintelligence/azure-ai-documentintelligence/samples/sample_forms/forms/Invoice_1.pdf"

    client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
    poller = client.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(url_source=url), output_content_format=ContentFormat.MARKDOWN)

    continuation_token = poller.continuation_token()
    encoded_token = base64.b64encode(continuation_token.encode()).decode()
    print(f"Continuation Token: {encoded_token}")

def read_documents(encoded_token):
    endpoint = os.getenv("AZURE_ENDPOINT", "https://default.cognitiveservices.azure.com/")
    key = os.getenv("AZURE_KEY", "default_key")

    continuation_token = base64.b64decode(encoded_token).decode()
    client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))

    polling_method = LROBasePolling()
    new_poller = LROPoller.from_continuation_token(
        polling_method=polling_method,
        continuation_token=continuation_token,
        deserialization_callback=deserialize_analyze_result,
        client=client._client
    )
    
    result = new_poller.result()
    print(f"Here's the content: {result.content_format}:\n{result.content}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze or read document intelligence results.")
    parser.add_argument("step", choices=["analyze", "read"], help="Step to execute: 'analyze' or 'read'")
    parser.add_argument("--token", help="Base64 encoded continuation token for the 'read' step")

    args = parser.parse_args()

    if args.step == "analyze":
        analyze_documents()
    elif args.step == "read":
        if not args.token:
            raise ValueError("The 'read' step requires a continuation token provided with --token")
        read_documents(args.token)