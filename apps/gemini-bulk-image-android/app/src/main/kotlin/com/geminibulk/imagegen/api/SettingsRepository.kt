package com.geminibulk.imagegen.api

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SettingsRepository(context: Context) {
    private val appContext = context.applicationContext
    private val prefs: SharedPreferences by lazy { createPrefs() }

    private fun createPrefs(): SharedPreferences {
        return try {
            EncryptedSharedPreferences.create(
                appContext,
                PREFS_NAME,
                MasterKey.Builder(appContext)
                    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                    .build(),
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
        } catch (ex: Exception) {
            Log.w(TAG, "EncryptedSharedPreferences unavailable; using standard prefs", ex)
            appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        }
    }

    fun getApiKey(): String = prefs.getString(KEY_API, "").orEmpty()

    fun saveApiKey(value: String): Result<Unit> {
        return try {
            prefs.edit().putString(KEY_API, value.trim()).apply()
            Result.success(Unit)
        } catch (ex: Exception) {
            Log.e(TAG, "Failed to save API key", ex)
            Result.failure(ex)
        }
    }

    fun getSelectedModelId(): String = prefs.getString(KEY_MODEL, "").orEmpty()

    fun saveSelectedModelId(value: String) {
        prefs.edit().putString(KEY_MODEL, value).apply()
    }

    fun getParallelEnabled(): Boolean = prefs.getBoolean(KEY_PARALLEL, false)

    fun saveParallelEnabled(value: Boolean) {
        prefs.edit().putBoolean(KEY_PARALLEL, value).apply()
    }

    fun getMaxParallelism(): Int = prefs.getInt(KEY_MAX_PARALLEL, DEFAULT_PARALLELISM)

    fun saveMaxParallelism(value: Int) {
        prefs.edit().putInt(KEY_MAX_PARALLEL, value.coerceIn(1, 8)).apply()
    }

    companion object {
        private const val TAG = "SettingsRepository"
        private const val PREFS_NAME = "gemini_bulk_secure_prefs"
        private const val KEY_API = "api_key"
        private const val KEY_MODEL = "selected_model"
        private const val KEY_PARALLEL = "parallel_enabled"
        private const val KEY_MAX_PARALLEL = "max_parallelism"
        const val DEFAULT_PARALLELISM = 3
    }
}
