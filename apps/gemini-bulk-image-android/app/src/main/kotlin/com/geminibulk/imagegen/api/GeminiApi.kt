package com.geminibulk.imagegen.api

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface GeminiApi {
    @GET("v1beta/models")
    suspend fun listModels(
        @Query("key") apiKey: String,
        @Query("pageSize") pageSize: Int = 100,
        @Query("pageToken") pageToken: String? = null,
    ): ModelsListResponse

    @POST("v1beta/models/{model}:generateContent")
    suspend fun generateContent(
        @Path("model") model: String,
        @Query("key") apiKey: String,
        @Body request: GenerateContentRequest,
    ): GenerateContentResponse
}

class GeminiApiFactory {
    fun create(apiKey: String): GeminiApi {
        val authInterceptor = Interceptor { chain ->
            val request = chain.request().newBuilder()
                .header("x-goog-api-key", apiKey)
                .build()
            chain.proceed(request)
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val client = OkHttpClient.Builder()
            .connectTimeout(120, TimeUnit.SECONDS)
            .readTimeout(180, TimeUnit.SECONDS)
            .writeTimeout(120, TimeUnit.SECONDS)
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .build()

        val moshi = Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(GeminiApi::class.java)
    }

    companion object {
        const val BASE_URL = "https://generativelanguage.googleapis.com/"
    }
}

class GeminiRepository(private val api: GeminiApi) {
    suspend fun fetchAllModels(apiKey: String): List<GeminiModelInfo> {
        val all = mutableListOf<GeminiModelInfo>()
        var pageToken: String? = null
        do {
            val response = api.listModels(apiKey = apiKey, pageToken = pageToken)
            all += response.models.orEmpty()
            pageToken = response.nextPageToken
        } while (!pageToken.isNullOrBlank())
        return all
    }

    suspend fun generateImage(
        apiKey: String,
        modelId: String,
        prompt: String,
        baseImage: EncodedImage,
        targetImage: EncodedImage,
    ): GenerateContentResponse {
        val request = GenerateContentRequest(
            contents = listOf(
                Content(
                    parts = listOf(
                        Part(text = prompt),
                        Part(
                            inlineData = InlineData(
                                mimeType = baseImage.mimeType,
                                data = baseImage.base64,
                            ),
                        ),
                        Part(
                            inlineData = InlineData(
                                mimeType = targetImage.mimeType,
                                data = targetImage.base64,
                            ),
                        ),
                    ),
                ),
            ),
            generationConfig = GenerationConfig(
                responseModalities = listOf("TEXT", "IMAGE"),
            ),
        )
        return api.generateContent(model = modelId, apiKey = apiKey, request = request)
    }
}

data class EncodedImage(
    val mimeType: String,
    val base64: String,
    val displayName: String,
)
