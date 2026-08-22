package com.geminibulk.imagegen.domain

import com.geminibulk.imagegen.api.EncodedImage
import com.geminibulk.imagegen.api.GenerateContentResponse
import com.geminibulk.imagegen.api.GeminiRepository
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit

enum class JobStatus {
    PENDING,
    RUNNING,
    SUCCESS,
    FAILED,
}

data class GenerationJob(
    val index: Int,
    val targetImage: EncodedImage,
    val status: JobStatus = JobStatus.PENDING,
    val errorMessage: String? = null,
    val outputMimeType: String? = null,
    val outputBase64: String? = null,
    val savedUri: String? = null,
)

data class BulkGenerationResult(
    val jobs: List<GenerationJob>,
)

class BulkGenerationEngine(
    private val repository: GeminiRepository,
) {
    suspend fun run(
        apiKey: String,
        modelId: String,
        prompt: String,
        baseImage: EncodedImage,
        targetImages: List<EncodedImage>,
        parallel: Boolean,
        maxParallelism: Int,
        onProgress: suspend (GenerationJob) -> Unit,
    ): BulkGenerationResult = coroutineScope {
        val jobs = targetImages.mapIndexed { index, image ->
            GenerationJob(index = index, targetImage = image)
        }.toMutableList()

        suspend fun executeJob(index: Int): GenerationJob {
            val target = targetImages[index]
            onProgress(jobs[index].copy(status = JobStatus.RUNNING))

            return try {
                val response = repository.generateImage(
                    apiKey = apiKey,
                    modelId = modelId,
                    prompt = prompt,
                    baseImage = baseImage,
                    targetImage = target,
                )
                val extracted = extractImage(response)
                val success = jobs[index].copy(
                    status = JobStatus.SUCCESS,
                    outputMimeType = extracted.first,
                    outputBase64 = extracted.second,
                )
                onProgress(success)
                success
            } catch (ex: Exception) {
                val failed = jobs[index].copy(
                    status = JobStatus.FAILED,
                    errorMessage = sanitizeError(ex.message ?: ex.toString()),
                )
                onProgress(failed)
                failed
            }
        }

        val results = if (parallel) {
            val semaphore = Semaphore(maxParallelism.coerceAtLeast(1))
            jobs.indices.map { index ->
                async {
                    semaphore.withPermit { executeJob(index) }
                }
            }.awaitAll()
        } else {
            jobs.indices.map { index -> executeJob(index) }
        }

        BulkGenerationResult(jobs = results)
    }

    private fun extractImage(response: GenerateContentResponse): Pair<String, String> {
        val parts = response.candidates
            ?.firstOrNull()
            ?.content
            ?.parts
            .orEmpty()

        val imagePart = parts.firstOrNull { it.inlineData != null }?.inlineData
            ?: throw IllegalStateException("No image returned in API response")

        return imagePart.mimeType to imagePart.data
    }

    private fun sanitizeError(message: String): String {
        return message
            .replace(Regex("(?i)(api[_-]?key|key=)[^\\s\"']+"), "$1[REDACTED]")
            .take(500)
    }
}
