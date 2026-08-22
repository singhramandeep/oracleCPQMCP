package com.geminibulk.imagegen

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.geminibulk.imagegen.ui.GeminiBulkScreen
import com.geminibulk.imagegen.ui.theme.GeminiBulkTheme
import com.geminibulk.imagegen.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            GeminiBulkTheme {
                GeminiBulkScreen(viewModel = viewModel())
            }
        }
    }
}
