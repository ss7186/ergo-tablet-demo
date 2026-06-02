# 다축 에르고미터 — Android WebView Wrapper

병원 헬스장용 안드로이드 태블릿 키오스크 앱. HF Space URL을 WebView로 로드.

## 기능

- 🚲 https://huggingface.co/spaces/OrthoEngine/ergo-tablet-demo 풀스크린 로드
- 💡 화면 항상 켜짐 (`FLAG_KEEP_SCREEN_ON`)
- 🔒 중간 키오스크 — 뒤로 버튼 차단 + huggingface.co 외부 URL 차단
- 🔄 30분마다 자동 새로고침 (sleep 방지 + 데이터 fresh)
- 🎥 영상/터치/JavaScript 모두 활성
- 📱 가로 모드 강제 (스탠바이미·태블릿용)

## APK 다운로드 (Android Studio 설치 불필요)

GitHub Actions가 자동으로 빌드:

1. https://github.com/ss7186/ergo-tablet-demo/actions
2. 가장 최신 **Build Android APK** workflow 클릭
3. 페이지 하단 **Artifacts** 섹션:
   - `ergo-tablet-debug.apk` — 개발/테스트용
   - `ergo-tablet-release.apk` — 운영 배포용 (debug signing — Google Play 배포는 별도 keystore 필요)
4. 다운로드 → .apk 추출

## 안드로이드 디바이스에 설치

1. 태블릿 → 설정 → **출처를 알 수 없는 앱 설치 허용** ON
2. .apk를 USB/이메일/Google Drive로 디바이스에 전송
3. 파일 매니저 → .apk 탭 → 설치
4. 앱 실행 → 자동으로 HF Space 로드

## 키오스크 강화 (선택)

기본 앱은 중간 수준 키오스크. 직원이 홈 버튼 누르면 빠져나갈 수 있음. 강한 잠금이 필요하면:

### A. 안드로이드 Screen Pinning (간단)
- 설정 → 보안 → 화면 고정 ON
- 앱 실행 후 최근 앱 → 압정 아이콘 → 화면 고정
- 종료: 뒤로 + 최근 동시 누르면

### B. Fully Kiosk Browser와 함께 사용
- 무료 Fully Kiosk Browser 설치
- "Start URL" = 본 앱 또는 HF URL
- PIN 잠금, 자동 새로고침, 화면 끄짐 방지

## 로컬 빌드 (개발자용)

Android Studio Hedgehog (2023.1.1) 이상 + JDK 17:

```bash
cd android
./gradlew assembleDebug
# → app/build/outputs/apk/debug/app-debug.apk
```

또는 release 빌드:
```bash
./gradlew assembleRelease
# → app/build/outputs/apk/release/app-release.apk
```

## URL 변경

`MainActivity.kt`의 `TARGET_URL` 상수를 다른 URL로 바꾸고 다시 빌드. 또는 GitHub에 push하면 GitHub Actions가 자동으로 새 APK 빌드.

## 트러블슈팅

| 문제 | 해결 |
|---|---|
| 흰 화면만 보임 | WiFi 확인. HF Space sleep 상태면 30초 wakeup 필요 |
| 영상 자동재생 안 됨 | `mediaPlaybackRequiresUserGesture = false` 이미 설정. WiFi 속도 확인 |
| 앱 설치 시 "Parse error" | Android 6.0+ 필요 (minSdk 23). 더 낮으면 `minSdk` 낮춰서 재빌드 |
| 뒤로 버튼이 빠져나감 | 정상 — 이번 빌드는 중간 키오스크. 더 강한 잠금은 위 §키오스크 강화 참고 |

## 라이센스

내부 데모용. 외부 배포 시 별도 서명 필요.
