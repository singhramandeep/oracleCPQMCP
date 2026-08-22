package com.geminibulk.imagegen.viewmodel

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.geminibulk.imagegen.api.CategorizedModel
import com.geminibulk.imagegen.api.EncodedImage
import com.geminibulk.imagegen.api.GeminiApiFactory
import com.geminibulk.imagegen.api.GeminiRepository
import com.geminibulk.imagegen.api.ModelCategorizer
import com.geminibulk.imagegen.api.ModelTask
import com.geminibulk.imagegen.api.SettingsRepository
import com.geminibulk.imagegen.domain.BulkGenerationEngine
import com.geminibulk.imagegen.domain.GenerationJob
import com.geminibulk.imagegen.domain.ImageSaver
import com.geminibulk.imagegen.domain.ImageUriLoader
import com.geminibulk.imagegen.domain.JobStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SelectedImage(
    val uri: Uri,
    val name: String,
)

data class MainUiState(
    val apiKey: String = "",
    val prompt: String = "",
    val models: List<CategorizedModel> = emptyList(),
    val selectedModelId: String = "",
    val taskFilter: ModelTask? = null,
    val baseImage: SelectedImage? = null,
    val targetImages: List<SelectedImage> = emptyList(),
    val parallelEnabled: Boolean = false,
    val maxParallelism: Int = SettingsRepository.DEFAULT_PARALLELISM,
    val jobs: List<GenerationJob> = emptyList(),
    val isLoadingModels: Boolean = false,
    val isGenerating: Boolean = false,
    val isApiKeySaved: Boolean = false,
    val statusMessage: String? = null,
    val errorMessage: String? = null,
    val snackbarMessage: String? = null,
)

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val settings = SettingsRepository(application)
    private val imageLoader = ImageUriLoader(application)
    private val imageSaver = ImageSaver(application)

    private val _uiState = MutableStateFlow(
        MainUiState(
            apiKey = runCatching { settings.getApiKey() }.getOrDefault(""),
            selectedModelId = runCatching { settings.getSelectedModelId() }.getOrDefault(""),
            parallelEnabled = runCatching { settings.getParallelEnabled() }.getOrDefault(false),
            maxParallelism = runCatching { settings.getMaxParallelism() }
                .getOrDefault(SettingsRepository.DEFAULT_PARALLELISM),
            isApiKeySaved = runCatching { settings.getApiKey().isNotBlank() }.getOrDefault(false),
        ),
    )
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()

    fun updateApiKey(value: String) {
        _uiState.update {
            it.copy(
                apiKey = value,
                isApiKeySaved = false,
            )
        }
    }

    fun saveApiKey() {
        val trimmed = _uiState.value.apiKey.trim()
        if (trimmed.isBlank()) {
            _uiState.update {
                it.copy(
                    isApiKeySaved = false,
                    errorMessage = "Enter your Gemini API key before saving.",
                    snackbarMessage = "Enter your Gemini API key before saving.",
                )
            }
            return
        }

        settings.saveApiKey(trimmed).fold(
            onSuccess = {
                _uiState.update {
                    it.copy(
                        apiKey = trimmed,
                        isApiKeySaved = true,
                        errorMessage = null,
                        statusMessage = "API key saved",
                        snackbarMessage = "API key saved successfully",
                    )
                }
            },
            onFailure = { ex ->
                _uiState.update {
                    it.copy(
                        isApiKeySaved = false,
                        errorMessage = ex.message ?: "Failed to save API key",
                        snackbarMessage = "Failed to save API key",
                    )
                }
            },
        )
    }

    fun updatePrompt(value: String) {
        _uiState.update { it.copy(prompt = value) }
    }

    fun setTaskFilter(task: ModelTask?) {
        _uiState.update { it.copy(taskFilter = task) }
    }

    fun selectModel(modelId: String) {
        settings.saveSelectedModelId(modelId)
        _uiState.update { it.copy(selectedModelId = modelId) }
    }

    fun setParallelEnabled(enabled: Boolean) {
        settings.saveParallelEnabled(enabled)
        _uiState.update { it.copy(parallelEnabled = enabled) }
    }

    fun setMaxParallelism(value: Int) {
        val clamped = value.coerceIn(1, 8)
        settings.saveMaxParallelism(clamped)
        _uiState.update { it.copy(maxParallelism = clamped) }
    }

    fun setBaseImage(uri: Uri, name: String) {
        _uiState.update { it.copy(baseImage = SelectedImage(uri, name)) }
    }

    fun addTargetImages(items: List<SelectedImage>) {
        _uiState.update { state ->
            val merged = (state.targetImages + items).distinctBy { it.uri }
            state.copy(targetImages = merged)
        }
    }

    fun removeTargetImage(uri: Uri) {
        _uiState.update { state ->
            state.copy(targetImages = state.targetImages.filterNot { it.uri == uri })
        }
    }

    fun clearTargets() {
        _uiState.update { it.copy(targetImages = emptyList(), jobs = emptyList()) }
    }

    fun loadModels() {
        val apiKey = _uiState.value.apiKey.trim()
        if (apiKey.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Enter and save your Gemini API key first.") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoadingModels = true, errorMessage = null) }
            try {
                val api = GeminiApiFactory().create(apiKey)
                val repository = GeminiRepository(api)
                val raw = repository.fetchAllModels(apiKey)
                val categorized = ModelCategorizer.categorize(raw)
                val imageModels = ModelCategorizer.imageCapableModels(categorized)
                val selected = when {
                    _uiState.value.selectedModelId.isNotBlank() &&
                        categorized.any { it.info.modelId == _uiState.value.selectedModelId } ->
                        _uiState.value.selectedModelId
                    imageModels.isNotEmpty() -> imageModels.first().info.modelId
                    categorized.isNotEmpty() -> categorized.first().info.modelId
                    else -> ""
                }
                if (selected.isNotBlank()) {
                    settings.saveSelectedModelId(selected)
                }
                _uiState.update {
                    it.copy(
                        models = categorized,
                        selectedModelId = selected,
                        isLoadingModels = false,
                        statusMessage = "Loaded ${categorized.size} models",
                    )
                }
            } catch (ex: Exception) {
                _uiState.update {
                    it.copy(
                        isLoadingModels = false,
                        errorMessage = ex.message ?: "Failed to load models",
                    )
                }
            }
        }
    }

    fun startBulkGeneration() {
        val state = _uiState.value
        val apiKey = state.apiKey.trim()
        val modelId = state.selectedModelId
        val prompt = state.prompt.trim()
        val base = state.baseImage
        val targets = state.targetImages

        when {
            apiKey.isBlank() -> {
                _uiState.update { it.copy(errorMessage = "API key is required.") }
                return
            }
            modelId.isBlank() -> {
                _uiState.update { it.copy(errorMessage = "Select a model first. Tap Load Models.") }
                return
            }
            prompt.isBlank() -> {
                _uiState.update { it.copy(errorMessage = "Enter a prompt.") }
                return
            }
            base == null -> {
                _uiState.update { it.copy(errorMessage = "Select one base/source image.") }
                return
            }
            targets.isEmpty() -> {
                _uiState.update { it.copy(errorMessage = "Select at least one target image.") }
                return
            }
        }

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isGenerating = true,
                    errorMessage = null,
                    statusMessage = "Preparing ${targets.size} requests...",
                    jobs = targets.mapIndexed { index, image ->
                        GenerationJob(
                            index = index,
                            targetImage = EncodedImage("", "", image.name),
                        )
                    },
                )
            }

            try {
                val encodedBase = imageLoader.encode(base.uri, base.name)
                val encodedTargets = targets.map { imageLoader.encode(it.uri, it.name) }

                val api = GeminiApiFactory().create(apiKey)
                val repository = GeminiRepository(api)
                val engine = BulkGenerationEngine(repository)

                val result = engine.run(
                    apiKey = apiKey,
                    modelId = modelId,
                    prompt = prompt,
                    baseImage = encodedBase,
                    targetImages = encodedTargets,
                    parallel = state.parallelEnabled,
                    maxParallelism = state.maxParallelism,
                ) { job ->
                    _uiState.update { current ->
                        val updated = current.jobs.toMutableList()
                        if (updated.size <= job.index) {
                            repeat(job.index - updated.size + 1) {
                                updated.add(
                                    GenerationJob(
                                        index = updated.size,
                                        targetImage = EncodedImage("", "", ""),
                                    ),
                                )
                            }
                        }
                        updated[job.index] = job
                        current.copy(jobs = updated.toList())
                    }
                }

                val successCount = result.jobs.count { it.status == JobStatus.SUCCESS }
                _uiState.update {
                    it.copy(
                        isGenerating = false,
                        jobs = result.jobs,
                        statusMessage = "Done: $successCount/${result.jobs.size} succeeded",
                    )
                }
            } catch (ex: Exception) {
                _uiState.update {
                    it.copy(
                        isGenerating = false,
                        errorMessage = ex.message ?: "Bulk generation failed",
                    )
                }
            }
        }
    }

    fun downloadJob(index: Int) {
        val job = _uiState.value.jobs.getOrNull(index) ?: return
        val base64 = job.outputBase64 ?: return
        val mimeType = job.outputMimeType ?: "image/png"

        viewModelScope.launch {
            try {
                val bytes = imageSaver.decodeBase64Image(base64, mimeType)
                val extension = when {
                    mimeType.contains("jpeg") || mimeType.contains("jpg") -> "jpg"
                    mimeType.contains("webp") -> "webp"
                    else -> "png"
                }
                val fileName = "gemini_${job.index + 1}_${System.currentTimeMillis()}.$extension"
                val uri = imageSaver.saveToDownloads(bytes, fileName, mimeType)
                _uiState.update { state ->
                    val jobs = state.jobs.toMutableList()
                    jobs[index] = job.copy(savedUri = uri.toString())
                    state.copy(
                        jobs = jobs,
                        statusMessage = "Saved ${job.targetImage.displayName} to Pictures/GeminiBulk",
                    )
                }
            } catch (ex: Exception) {
                _uiState.update {
                    it.copy(errorMessage = ex.message ?: "Failed to save image")
                }
            }
        }
    }

    fun downloadAllSuccessful() {
        _uiState.value.jobs.forEachIndexed { index, job ->
            if (job.status == JobStatus.SUCCESS && job.savedUri == null) {
                downloadJob(index)
            }
        }
    }

    fun clearMessages() {
        _uiState.update { it.copy(statusMessage = null, errorMessage = null) }
    }

    fun clearSnackbarMessage() {
        _uiState.update { it.copy(snackbarMessage = null) }
    }
}
