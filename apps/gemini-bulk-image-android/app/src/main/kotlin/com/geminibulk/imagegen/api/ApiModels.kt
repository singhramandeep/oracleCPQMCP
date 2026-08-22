package com.geminibulk.imagegen.api

import com.squareup.moshi.Json

data class ModelsListResponse(
    val models: List<GeminiModelInfo>? = null,
    @Json(name = "nextPageToken") val nextPageToken: String? = null,
)

data class GeminiModelInfo(
    val name: String,
    @Json(name = "displayName") val displayName: String? = null,
    val description: String? = null,
    @Json(name = "supportedGenerationMethods")
    val supportedGenerationMethods: List<String>? = null,
    @Json(name = "inputTokenLimit") val inputTokenLimit: Int? = null,
    @Json(name = "outputTokenLimit") val outputTokenLimit: Int? = null,
) {
    val modelId: String
        get() = name.removePrefix("models/")
}

enum class ModelTask {
    IMAGE,
    CODING,
    TEXT,
    MULTIMODAL,
}

data class CategorizedModel(
    val info: GeminiModelInfo,
    val tasks: Set<ModelTask>,
)

data class GenerateContentRequest(
    val contents: List<Content>,
    @Json(name = "generationConfig") val generationConfig: GenerationConfig? = null,
)

data class Content(
    val role: String = "user",
    val parts: List<Part>,
)

data class Part(
    val text: String? = null,
    @Json(name = "inlineData") val inlineData: InlineData? = null,
)

data class InlineData(
    @Json(name = "mimeType") val mimeType: String,
    val data: String,
)

data class GenerationConfig(
    @Json(name = "responseModalities") val responseModalities: List<String>? = null,
)

data class GenerateContentResponse(
    val candidates: List<Candidate>? = null,
    @Json(name = "promptFeedback") val promptFeedback: PromptFeedback? = null,
)

data class Candidate(
    val content: Content? = null,
    @Json(name = "finishReason") val finishReason: String? = null,
)

data class PromptFeedback(
    @Json(name = "blockReason") val blockReason: String? = null,
)

data class ApiErrorResponse(
    val error: ApiErrorBody? = null,
)

data class ApiErrorBody(
    val code: Int? = null,
    val message: String? = null,
    val status: String? = null,
)
