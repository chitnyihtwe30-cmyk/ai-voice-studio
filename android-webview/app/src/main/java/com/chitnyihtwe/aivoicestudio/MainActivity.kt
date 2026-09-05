package com.chitnyihtwe.aivoicestudio

import android.app.Activity
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import java.util.Locale

class MainActivity : Activity(), TextToSpeech.OnInitListener {
    private lateinit var webView: WebView
    private lateinit var tts: TextToSpeech

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tts = TextToSpeech(this, this)
        webView = WebView(this)
        setContentView(webView)
        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            allowFileAccess = true
            allowContentAccess = true
        }
        webView.webViewClient = WebViewClient()
        webView.webChromeClient = WebChromeClient()
        webView.addJavascriptInterface(LocalTtsBridge(), "AndroidTTS")
        webView.loadUrl("file:///android_asset/index.html")
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts.language = Locale.US
        }
    }

    inner class LocalTtsBridge {
        @JavascriptInterface
        fun speak(text: String, language: String, rate: Float) {
            val locale = if (language.startsWith("my")) Locale("my", "MM") else Locale.US
            val result = tts.setLanguage(locale)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                runOnUiThread { webView.evaluateJavascript("window.localTtsError && window.localTtsError()", null) }
                return
            }
            tts.setSpeechRate(rate.coerceIn(0.5f, 2f))
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "local-voice")
            runOnUiThread { webView.evaluateJavascript("window.localTtsStarted && window.localTtsStarted()", null) }
        }

        @JavascriptInterface
        fun stop() {
            tts.stop()
        }
    }

    override fun onDestroy() {
        if (::tts.isInitialized) {
            tts.stop()
            tts.shutdown()
        }
        if (::webView.isInitialized) webView.destroy()
        super.onDestroy()
    }
}
