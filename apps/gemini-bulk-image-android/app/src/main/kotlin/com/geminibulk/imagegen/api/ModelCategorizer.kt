package com.geminibulk.imagegen.api

object ModelCategorizer {
    fun categorize(models: List<GeminiModelInfo>): List<CategorizedModel> {
        return models
            .filter { it.supportedGenerationMethods?.contains("generateContent") == true }
            .map { model ->
                CategorizedModel(info = model, tasks = inferTasks(model))
            }
            .sortedBy { it.info.displayName ?: it.info.modelId }
    }

    fun inferTasks(model: GeminiModelInfo): Set<ModelTask> {
        val id = model.modelId.lowercase()
        val description = model.description?.lowercase().orEmpty()
        val display = model.displayName?.lowercase().orEmpty()
        val combined = "$id $description $display"

        val tasks = linkedSetOf<ModelTask>()

        if (isImageModel(combined)) {
            tasks += ModelTask.IMAGE
        }
        if (isCodingModel(combined)) {
            tasks += ModelTask.CODING
        }
        if (isMultimodalModel(combined)) {
            tasks += ModelTask.MULTIMODAL
        }
        if (tasks.isEmpty() || (!isImageModel(combined) && supportsText(combined))) {
            tasks += ModelTask.TEXT
        }

        return tasks
    }

    fun imageCapableModels(categorized: List<CategorizedModel>): List<CategorizedModel> {
        return categorized.filter { ModelTask.IMAGE in it.tasks || ModelTask.MULTIMODAL in it.tasks }
    }

    private fun isImageModel(value: String): Boolean {
        return value.contains("image") ||
            value.contains("imagen") ||
            value.contains("nano banana")
    }

    private fun isCodingModel(value: String): Boolean {
        return value.contains("code") || value.contains("coder")
    }

    private fun isMultimodalModel(value: String): Boolean {
        return value.contains("vision") ||
            value.contains("multimodal") ||
            (value.contains("flash") && !isImageModel(value) && value.contains("pro"))
    }

    private fun supportsText(value: String): Boolean {
        return !value.contains("embedding") && !value.contains("aqa")
    }
}
