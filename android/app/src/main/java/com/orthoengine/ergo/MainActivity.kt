package com.orthoengine.ergo

import android.annotation.SuppressLint
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.KeyEvent
import android.view.View
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

/**
 * 다축 에르고미터 — WebView wrapper
 *
 * 기능:
 *  - Hugging Face Space URL 로드
 *  - 화면 항상 켜짐 (sleep 차단)
 *  - 풀스크린 immersive 모드
 *  - 뒤로 버튼 차단 (중간 키오스크)
 *  - 30분마다 자동 새로고침 (sleep 방지 + 데이터 fresh)
 *  - 영상/터치/JavaScript 모두 활성
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val handler = Handler(Looper.getMainLooper())

    companion object {
        const val TARGET_URL = "https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo"
        const val REFRESH_INTERVAL_MS = 30L * 60L * 1000L  // 30분
    }

    private val autoRefresh = object : Runnable {
        override fun run() {
            webView.reload()
            handler.postDelayed(this, REFRESH_INTERVAL_MS)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 화면 항상 켜기
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        applyImmersive()

        webView = findViewById(R.id.webView)
        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            useWideViewPort = true
            loadWithOverviewMode = true
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
            // 영상/오디오 자동 재생 허용
            mediaPlaybackRequiresUserGesture = false
        }

        webView.webViewClient = object : WebViewClient() {
            // 외부 도메인 이탈 차단 (중간 키오스크: huggingface.co 도메인만)
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: android.webkit.WebResourceRequest?
            ): Boolean {
                val url = request?.url?.toString() ?: return false
                return if (url.contains("huggingface.co") || url.contains("hf.space")) {
                    false  // 내부 navigation 허용
                } else {
                    true  // 외부 URL 차단
                }
            }
        }
        webView.webChromeClient = WebChromeClient()

        webView.loadUrl(TARGET_URL)
        handler.postDelayed(autoRefresh, REFRESH_INTERVAL_MS)
    }

    private fun applyImmersive() {
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            )
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) applyImmersive()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        // 뒤로 버튼 차단 (앱 종료 방지) — 중간 수준 키오스크
        if (keyCode == KeyEvent.KEYCODE_BACK) return true
        // Volume 키는 통과 (직원이 음량 조절)
        return super.onKeyDown(keyCode, event)
    }

    override fun onPause() {
        super.onPause()
        handler.removeCallbacks(autoRefresh)
    }

    override fun onResume() {
        super.onResume()
        handler.postDelayed(autoRefresh, REFRESH_INTERVAL_MS)
        applyImmersive()
    }

    override fun onDestroy() {
        handler.removeCallbacks(autoRefresh)
        webView.destroy()
        super.onDestroy()
    }
}
