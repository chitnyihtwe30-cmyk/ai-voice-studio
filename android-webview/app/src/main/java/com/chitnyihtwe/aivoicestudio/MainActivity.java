package com.chitnyihtwe.aivoicestudio;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int FILE_REQUEST = 1001;
    private static final String HOME_URL = "https://chitnyihtwe30-cmyk.github.io/ai-voice-studio/";
    private WebView webView;
    private ValueCallback<Uri[]> uploadCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            webView = new WebView(this);
            setContentView(webView);
            webView.getSettings().setJavaScriptEnabled(true);
            webView.getSettings().setDomStorageEnabled(true);
            webView.getSettings().setMediaPlaybackRequiresUserGesture(false);
            webView.getSettings().setAllowFileAccess(true);
            webView.getSettings().setAllowContentAccess(true);
            webView.getSettings().setJavaScriptCanOpenWindowsAutomatically(true);
            webView.setWebViewClient(new WebViewClient());
            webView.setWebChromeClient(new WebChromeClient() {
                @Override
                public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> callback, FileChooserParams params) {
                    if (uploadCallback != null) uploadCallback.onReceiveValue(null);
                    uploadCallback = callback;
                    try {
                        Intent intent = params.createIntent();
                        startActivityForResult(intent, FILE_REQUEST);
                        return true;
                    } catch (Exception e) {
                        uploadCallback = null;
                        Toast.makeText(MainActivity.this, "File picker မဖွင့်နိုင်ပါ", Toast.LENGTH_SHORT).show();
                        return false;
                    }
                }
            });
            webView.loadUrl(HOME_URL);
        } catch (Throwable e) {
            TextView error = new TextView(this);
            error.setText("AI Voice Studio\n\nApp စတင်ဖွင့်ရာတွင် WebView error ဖြစ်နေပါတယ်။\nAndroid System WebView / Chrome ကို update လုပ်ပြီး ပြန်စမ်းပါ။");
            error.setTextSize(18f);
            error.setPadding(32, 64, 32, 32);
            setContentView(error);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_REQUEST) {
            Uri[] result = null;
            if (resultCode == RESULT_OK && data != null) {
                result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
            }
            if (uploadCallback != null) uploadCallback.onReceiveValue(result);
            uploadCallback = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (uploadCallback != null) uploadCallback.onReceiveValue(null);
        uploadCallback = null;
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
        }
        super.onDestroy();
    }
}
