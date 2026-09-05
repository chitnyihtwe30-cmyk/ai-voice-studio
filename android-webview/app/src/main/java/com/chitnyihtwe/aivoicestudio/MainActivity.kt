package com.chitnyihtwe.aivoicestudio

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import java.io.File
import java.io.FileOutputStream
import java.util.Locale
import com.k2fsa.sherpa.onnx.*

class MainActivity : Activity(), TextToSpeech.OnInitListener {
    private lateinit var webView: WebView
    private lateinit var tts: TextToSpeech
    private var sampleUri: Uri? = null
    private var cloneTts: OfflineTts? = null
    private val pickRequest = 7001

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
        webView.addJavascriptInterface(LocalBridge(), "AndroidTTS")
        webView.loadUrl("file:///android_asset/index.html")
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) tts.language = Locale.US
    }

    inner class LocalBridge {
        @JavascriptInterface
        fun speak(text: String, language: String, rate: Float) {
            val locale = if (language.startsWith("my")) Locale("my", "MM") else Locale.US
            val result = tts.setLanguage(locale)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                ui("window.localTtsError&&window.localTtsError()")
                return
            }
            tts.setSpeechRate(rate.coerceIn(0.5f, 2f))
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "local-voice")
            ui("window.localTtsStarted&&window.localTtsStarted()")
        }

        @JavascriptInterface
        fun stop() { tts.stop(); cloneTts?.stop() }

        @JavascriptInterface
        fun pickSample() {
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "audio/wav"
            }
            startActivityForResult(intent, pickRequest)
        }

        @JavascriptInterface
        fun sampleName(): String = sampleUri?.lastPathSegment ?: ""

        @JavascriptInterface
        fun clone(text: String, referenceText: String, steps: Int) {
            val uri = sampleUri ?: run { ui("window.cloneError&&window.cloneError('Voice sample မရွေးရသေးပါ')"); return }
            Thread {
                try {
                    val sample = copySampleToCache(uri)
                    val modelDir = copyAssetTree("zipvoice", File(filesDir, "zipvoice"))
                    copyAssetTree("vocos_24khz.onnx", File(filesDir, "vocos_24khz.onnx"))
                    val cfg = OfflineTtsZipVoiceModelConfig.builder()
                        .setTokens(File(modelDir, "tokens.txt").path)
                        .setEncoder(File(modelDir, "encoder.int8.onnx").path)
                        .setDecoder(File(modelDir, "decoder.int8.onnx").path)
                        .setVocoder(File(filesDir, "vocos_24khz.onnx").path)
                        .setDataDir(File(modelDir, "espeak-ng-data").path)
                        .setLexicon(File(modelDir, "lexicon.txt").path)
                        .build()
                    val model = OfflineTtsModelConfig.builder().setZipvoice(cfg).setNumThreads(2).setDebug(false).build()
                    cloneTts?.release()
                    cloneTts = OfflineTts(OfflineTtsConfig.builder().setModel(model).build())
                    val reader = WaveReader(sample.path)
                    val gen = GenerationConfig().apply {
                        setReferenceAudio(reader.getSamples())
                        setReferenceSampleRate(reader.getSampleRate())
                        setReferenceText(referenceText)
                        setNumSteps(steps.coerceIn(2, 8))
                    }
                    val audio = cloneTts!!.generateWithConfigAndCallback(text, gen) { 1 }
                    val out = File(cacheDir, "clone-${System.currentTimeMillis()}.wav")
                    audio.save(out.path)
                    ui("window.cloneDone&&window.cloneDone('${out.toURI()}')")
                } catch (e: Exception) {
                    ui("window.cloneError&&window.cloneError(${js(e.message ?: e.javaClass.simpleName)})")
                }
            }.start()
        }
    }

    private fun copySampleToCache(uri: Uri): File {
        val out = File(cacheDir, "reference.wav")
        contentResolver.openInputStream(uri).use { input -> FileOutputStream(out).use { output -> input!!.copyTo(output) } }
        return out
    }

    private fun copyAssetTree(assetPath: String, destination: File): File {
        if (destination.exists()) return destination
        val children = assets.list(assetPath)
        if (children.isNullOrEmpty()) {
            destination.parentFile?.mkdirs()
            assets.open(assetPath).use { input -> FileOutputStream(destination).use { output -> input.copyTo(output) } }
            return destination
        }
        destination.mkdirs()
        for (child in children) copyAssetTree("$assetPath/$child", File(destination, child))
        return destination
    }

    private fun ui(js: String) = runOnUiThread { webView.evaluateJavascript(js, null) }
    private fun js(s: String): String = "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ") + "'"

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == pickRequest && resultCode == RESULT_OK) {
            sampleUri = data?.data
            ui("window.samplePicked&&window.samplePicked(${js(sampleUri?.lastPathSegment ?: "Voice sample selected")})")
        }
    }

    override fun onDestroy() {
        if (::tts.isInitialized) { tts.stop(); tts.shutdown() }
        cloneTts?.release()
        if (::webView.isInitialized) webView.destroy()
        super.onDestroy()
    }
}
