package com.geminibulk.imagegen.domain

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import com.geminibulk.imagegen.data.EncodedImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream

class ImageUriLoader(private val context: Context) {
    suspend fun encode(uri: Uri, displayName: String): EncodedImage = withContext(Dispatchers.IO) {
        context.contentResolver.openInputStream(uri)?.use { input ->
            val bytes = input.readBytes()
            val mimeType = context.contentResolver.getType(uri) ?: guessMimeType(displayName)
            EncodedImage(
                mimeType = mimeType,
                base64 = Base64.encodeToString(bytes, Base64.NO_WRAP),
                displayName = displayName,
            )
        } ?: error("Unable to read image: $displayName")
    }

    private fun guessMimeType(name: String): String {
        return when {
            name.endsWith(".png", ignoreCase = true) -> "image/png"
            name.endsWith(".webp", ignoreCase = true) -> "image/webp"
            name.endsWith(".gif", ignoreCase = true) -> "image/gif"
            else -> "image/jpeg"
        }
    }
}

class ImageSaver(private val context: Context) {
    suspend fun saveToDownloads(
        imageBytes: ByteArray,
        fileName: String,
        mimeType: String,
    ): Uri = withContext(Dispatchers.IO) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, mimeType)
                put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/GeminiBulk")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
                ?: error("Failed to create MediaStore entry")
            resolver.openOutputStream(uri)?.use { it.write(imageBytes) }
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
            uri
        } else {
            @Suppress("DEPRECATION")
            val dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES)
            val appDir = File(dir, "GeminiBulk").apply { mkdirs() }
            val file = File(appDir, fileName)
            FileOutputStream(file).use { it.write(imageBytes) }
            Uri.fromFile(file)
        }
    }

    fun decodeBase64Image(base64: String, mimeType: String): ByteArray {
        return Base64.decode(base64, Base64.DEFAULT)
    }

    fun decodeToBitmap(bytes: ByteArray): Bitmap? {
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    }
}
