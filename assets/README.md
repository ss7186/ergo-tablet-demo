# Media Assets

각 condition별 일러스트와 영상을 추가하는 위치.

## 파일 명명 규칙

condition 코드를 소문자로:

```
assets/
  illustrations/
    nene.png      또는 .svg / .jpg
    adne.png
    nead.png
    aene.png
    neae.png
    aine.png
    neai.png
    adad.png
    aeae.png
    aiai.png
    howto_main.png    # Welcome 사용법 안내용 메인 이미지
  videos/
    nene.mp4
    adne.mp4
    nead.mp4
    aene.mp4
    neae.mp4
    aine.mp4
    neai.mp4
    adad.mp4
    aeae.mp4
    aiai.mp4
    howto_main.mp4    # Welcome 사용법 메인 영상
```

## 영상 소스

원본: `[PROMOTION]/KakaoTalk_20260522_183104677.mp4`

각 condition별로 잘라서 위 경로에 `<condition_code>.mp4`로 저장하면 result 화면에 자동 표시됨.

대안: 외부 호스팅 (YouTube 등) URL을 `conditions.json`의 `media.video` 필드에 직접 넣어도 됨.

## Streamlit Cloud 배포 시 주의

mp4가 큰 경우 (>50MB) GitHub repo 용량 부담. 권장:
- 30초 이내 짧은 clip으로 자르기 (각 condition당)
- 또는 외부 호스팅 사용 (URL → `conditions.json`)
- Streamlit Cloud 무료는 git lfs 미지원

## 파일이 없을 때

`utils/media.py`가 file existence를 체크하므로, 파일 없으면 "준비 중" 메시지로 자동 대체. 깨지지 않음.
