package com.geminibulk.imagegen.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.HourglassEmpty
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.geminibulk.imagegen.api.CategorizedModel
import com.geminibulk.imagegen.api.ModelTask
import com.geminibulk.imagegen.domain.JobStatus
import com.geminibulk.imagegen.viewmodel.MainViewModel
import com.geminibulk.imagegen.viewmodel.SelectedImage

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun GeminiBulkScreen(viewModel: MainViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.errorMessage, state.statusMessage) {
        if (state.errorMessage != null || state.statusMessage != null) {
            kotlinx.coroutines.delay(5000)
            viewModel.clearMessages()
        }
    }

    val basePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia(),
    ) { uri ->
        if (uri != null) {
            viewModel.setBaseImage(uri, uri.lastPathSegment ?: "base_image")
        }
    }

    val targetPicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickMultipleVisualMedia(maxItems = 50),
    ) { uris ->
        if (uris.isNotEmpty()) {
            viewModel.addTargetImages(
                uris.map { uri -> SelectedImage(uri, uri.lastPathSegment ?: uri.toString()) },
            )
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Gemini Bulk Image") })
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                SectionCard(title = "1. Gemini API Key") {
                    OutlinedTextField(
                        value = state.apiKey,
                        onValueChange = viewModel::updateApiKey,
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("API Key") },
                        visualTransformation = PasswordVisualTransformation(),
                        singleLine = true,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(onClick = viewModel::saveApiKey, modifier = Modifier.fillMaxWidth()) {
                        Text("Save API Key")
                    }
                }
            }

            item {
                SectionCard(title = "2. Models by Task") {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        OutlinedButton(
                            onClick = viewModel::loadModels,
                            enabled = !state.isLoadingModels,
                            modifier = Modifier.weight(1f),
                        ) {
                            if (state.isLoadingModels) {
                                CircularProgressIndicator(modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                            } else {
                                Icon(Icons.Default.Refresh, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                            }
                            Text("Load Models")
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilterChip(
                            selected = state.taskFilter == null,
                            onClick = { viewModel.setTaskFilter(null) },
                            label = { Text("All") },
                        )
                        ModelTask.entries.forEach { task ->
                            FilterChip(
                                selected = state.taskFilter == task,
                                onClick = {
                                    viewModel.setTaskFilter(if (state.taskFilter == task) null else task)
                                },
                                label = { Text(task.name.lowercase().replaceFirstChar { it.titlecase() }) },
                            )
                        }
                    }

                    val filtered = filteredModels(state.models, state.taskFilter)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Available: ${filtered.size}", style = MaterialTheme.typography.bodySmall)

                    filtered.take(20).forEach { model ->
                        ModelRow(
                            model = model,
                            selected = model.info.modelId == state.selectedModelId,
                            onSelect = { viewModel.selectModel(model.info.modelId) },
                        )
                    }
                    if (filtered.size > 20) {
                        Text(
                            "... and ${filtered.size - 20} more",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }

            item {
                SectionCard(title = "3. Prompt & Images") {
                    OutlinedTextField(
                        value = state.prompt,
                        onValueChange = viewModel::updatePrompt,
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Generation prompt") },
                        minLines = 3,
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedButton(
                        onClick = {
                            basePicker.launch(
                                PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                            )
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            if (state.baseImage == null) {
                                "Select base/source image (shared)"
                            } else {
                                "Base: ${state.baseImage?.name}"
                            },
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(
                        onClick = {
                            targetPicker.launch(
                                PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                            )
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Select target images (${state.targetImages.size})")
                    }

                    if (state.targetImages.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedButton(
                            onClick = viewModel::clearTargets,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text("Clear target images")
                        }
                    }
                }
            }

            item {
                SectionCard(title = "4. Execution") {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text("Parallel requests")
                        Switch(
                            checked = state.parallelEnabled,
                            onCheckedChange = viewModel::setParallelEnabled,
                        )
                    }
                    if (state.parallelEnabled) {
                        Text("Max parallel: ${state.maxParallelism}")
                        Slider(
                            value = state.maxParallelism.toFloat(),
                            onValueChange = { viewModel.setMaxParallelism(it.toInt()) },
                            valueRange = 1f..8f,
                            steps = 6,
                        )
                    } else {
                        Text(
                            "Serial mode runs one request at a time.",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Total requests: ${state.targetImages.size} " +
                            "(each = base image + one unique target + prompt)",
                        style = MaterialTheme.typography.bodySmall,
                    )

                    Spacer(modifier = Modifier.height(12.dp))
                    Button(
                        onClick = viewModel::startBulkGeneration,
                        enabled = !state.isGenerating && state.targetImages.isNotEmpty(),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Icon(Icons.Default.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            if (state.isGenerating) {
                                "Generating..."
                            } else {
                                "Start Bulk Generation"
                            },
                        )
                    }

                    if (state.isGenerating) {
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    }
                }
            }

            if (state.jobs.isNotEmpty()) {
                item {
                    SectionCard(title = "5. Results") {
                        val done = state.jobs.count {
                            it.status == JobStatus.SUCCESS || it.status == JobStatus.FAILED
                        }
                        Text("Progress: $done / ${state.jobs.size}")
                        Spacer(modifier = Modifier.height(8.dp))
                        Button(
                            onClick = viewModel::downloadAllSuccessful,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(Icons.Default.Download, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Download all successful")
                        }
                    }
                }

                itemsIndexed(state.jobs) { index, job ->
                    JobResultCard(
                        jobIndex = index,
                        targetName = job.targetImage.displayName,
                        status = job.status,
                        errorMessage = job.errorMessage,
                        savedUri = job.savedUri,
                        previewBase64 = job.outputBase64,
                        previewMime = job.outputMimeType,
                        onDownload = { viewModel.downloadJob(index) },
                    )
                }
            }

            state.statusMessage?.let { message ->
                item {
                    Text(message, color = MaterialTheme.colorScheme.secondary)
                }
            }
            state.errorMessage?.let { message ->
                item {
                    Text(message, color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }
}

@Composable
private fun SectionCard(
    title: String,
    content: @Composable () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(12.dp))
            content()
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ModelRow(
    model: CategorizedModel,
    selected: Boolean,
    onSelect: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        onClick = onSelect,
        colors = CardDefaults.cardColors(
            containerColor = if (selected) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surfaceVariant
            },
        ),
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                model.info.displayName ?: model.info.modelId,
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(model.info.modelId, style = MaterialTheme.typography.bodySmall)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                model.tasks.forEach { task ->
                    AssistChip(
                        onClick = {},
                        label = { Text(task.name.lowercase()) },
                    )
                }
            }
        }
    }
}

@Composable
private fun JobResultCard(
    jobIndex: Int,
    targetName: String,
    status: JobStatus,
    errorMessage: String?,
    savedUri: String?,
    previewBase64: String?,
    previewMime: String?,
    onDownload: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusIcon(status)
                Spacer(modifier = Modifier.width(8.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Request #${jobIndex + 1}")
                    Text(targetName, style = MaterialTheme.typography.bodySmall)
                }
                if (status == JobStatus.SUCCESS) {
                    IconButton(onClick = onDownload) {
                        Icon(Icons.Default.Download, contentDescription = "Download")
                    }
                }
            }
            when (status) {
                JobStatus.FAILED -> Text(errorMessage.orEmpty(), color = MaterialTheme.colorScheme.error)
                JobStatus.SUCCESS -> {
                    if (savedUri != null) {
                        Text("Saved", style = MaterialTheme.typography.bodySmall)
                    }
                    previewBase64?.let { base64 ->
                        val uri = Uri.parse(
                            "data:${previewMime ?: "image/png"};base64,$base64",
                        )
                        AsyncImage(
                            model = uri,
                            contentDescription = "Generated preview",
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(180.dp)
                                .padding(top = 8.dp),
                            contentScale = ContentScale.Fit,
                        )
                    }
                }
                else -> Unit
            }
        }
    }
}

@Composable
private fun StatusIcon(status: JobStatus) {
    val icon = when (status) {
        JobStatus.PENDING -> Icons.Default.HourglassEmpty
        JobStatus.RUNNING -> Icons.Default.Refresh
        JobStatus.SUCCESS -> Icons.Default.CheckCircle
        JobStatus.FAILED -> Icons.Default.Error
    }
    val tint = when (status) {
        JobStatus.SUCCESS -> MaterialTheme.colorScheme.secondary
        JobStatus.FAILED -> MaterialTheme.colorScheme.error
        JobStatus.RUNNING -> MaterialTheme.colorScheme.primary
        JobStatus.PENDING -> MaterialTheme.colorScheme.outline
    }
    Icon(icon, contentDescription = status.name, tint = tint)
}

private fun filteredModels(
    models: List<CategorizedModel>,
    taskFilter: ModelTask?,
): List<CategorizedModel> {
    if (taskFilter == null) return models
    return models.filter { taskFilter in it.tasks }
}
