package com.chitnyihtwe.aivoicestudio

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.*
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private var uploadCallback: ValueCallback<Array<Uri>>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        try {
            webView = WebView(this)
            setContentView(webView)

            with(webView.settings) {
                javaScriptEnabled = true
                domStorageEnabled = true
                mediaPlaybackRequiresUserGesture = false
                allowFileAccess = true
                allowContentAccess = true
                javaScriptCanOpenWindowsAutomatically = true
            }

            webView.webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView?,
                    errorCode: Int,
                    description: String?,
                    failingUrl: String?
                ) {
                    super.onReceivedError(view, errorCode, description, failingUrl)
                }
            }

            webView.webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    v: WebView?,
                    callback: ValueCallback<Array<Uri>>?,
                    params: FileChooserParams?
                ): Boolean {
                    uploadCallback?.onReceiveValue(null)
                    uploadCallback = callback
                    return try {
                        val intent = params?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                            type = "audio/*"
                            addCategory(Intent.CATEGORY_OPENABLE)
                        }
                        startActivityForResult(intent, FILE_REQUEST)
                        true
                    } catch (e: Exception) {
                        uploadCallback = null
                        Toast.makeText(
                            this@MainActivity,
                            "File picker မဖွင့်နိုင်ပါ",
                            Toast.LENGTH_SHORT
                        ).show()
                        false
                    }
                }
            }

            webView.loadUrl(HOME_URL)
        } catch (e: Exception) {
            val message = TextView(this).apply {
                text = "AI Voice Studio\n\nApp စတင်ဖွင့်ရာတွင် error ဖြစ်နေပါတယ်။\nWebView/Chrome ကို update လုပ်ပြီး ပြန်စမ်းပါ။"
                textSize = 18f
                setPadding(32, 64, 32, 32)
            }
            setContentView(message)
        }
    }

    @Deprecated("Deprecated in Android API")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == FILE_REQUEST) {
            val result = if (resultCode == RESULT_OK && data != null) {
                WebChromeClient.FileChooserParams.parseResult(resultCode, data)
            } else null
            uploadCallback?.onReceiveValue(result)
            uploadCallback = null
        }
    }

    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    override fun onDestroy() {
        uploadCallback?.onReceiveValue(null)
        uploadCallback = null
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.destroy()
        }
        super.onDestroy()
    }

    companion object {
        private const val FILE_REQUEST = 1001
        private const val HOME_URL = "https://chitnyihtwe30-cmyk.github.io/ai-voice-studio/"
    }
}
