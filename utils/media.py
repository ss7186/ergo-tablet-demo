"""Media (영상/일러스트) 렌더 헬퍼. 파일 없을 때 안전한 fallback."""
import base64
from pathlib import Path
from typing import Optional
import streamlit as st


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def _resolve(rel_path: Optional[str]) -> Optional[Path]:
    """assets/ 기준 상대경로 또는 외부 URL을 받아 Path 또는 None."""
    if not rel_path:
        return None
    if rel_path.startswith(("http://", "https://")):
        return rel_path  # URL은 그대로 반환
    p = ASSETS_DIR / rel_path
    return p if p.exists() else None


def render_illustration(rel_path: Optional[str], caption: Optional[str] = None, width=None):
    """일러스트 표시. 없으면 placeholder.

    width: None → 'stretch' (container 폭에 맞춤), int → 픽셀, 'content' → 원본 크기.
    Streamlit 1.57+ 에서 None 금지.
    """
    resolved = _resolve(rel_path)
    if resolved is None:
        st.markdown(
            f'<div class="media-placeholder">🖼️ 일러스트 준비 중<br/><span class="media-hint">{rel_path or "(경로 없음)"}</span></div>',
            unsafe_allow_html=True,
        )
        return
    w = width if width is not None else "stretch"
    if isinstance(resolved, Path):
        st.image(str(resolved), caption=caption, width=w)
    else:
        st.image(resolved, caption=caption, width=w)


def render_video(rel_path: Optional[str], description: Optional[str] = None):
    """영상 표시. 없으면 description만 보여줌."""
    resolved = _resolve(rel_path)
    if resolved is None:
        if description:
            st.markdown(
                f'<div class="media-placeholder video"><div class="play-icon">▶</div>'
                f'<div class="media-desc">{description}</div>'
                f'<div class="media-hint">영상 준비 중 ({rel_path or "경로 없음"})</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="media-placeholder video">🎬 영상 준비 중<br/>'
                f'<span class="media-hint">{rel_path or "(경로 없음)"}</span></div>',
                unsafe_allow_html=True,
            )
        return
    if isinstance(resolved, Path):
        st.video(str(resolved))
    else:
        st.video(resolved)
    if description:
        st.caption(description)


def has_media(rel_path: Optional[str]) -> bool:
    return _resolve(rel_path) is not None


def render_illustration_fixed_height(rel_path: Optional[str], height: int = 320, caption: Optional[str] = None):
    """일러스트를 고정 높이로 표시. 다른 그림과 height를 맞출 때 사용.

    width는 자동(max 100%), object-fit: contain으로 비율 유지.
    """
    resolved = _resolve(rel_path)
    if resolved is None:
        st.markdown(
            f'<div class="illust-fixed" style="min-height:{height}px;">'
            f'<div class="media-placeholder small">🖼️ {rel_path or "준비 중"}</div></div>',
            unsafe_allow_html=True,
        )
        return
    if isinstance(resolved, Path):
        ext = resolved.suffix.lstrip(".").lower()
        if ext == "jpg":
            ext = "jpeg"
        b64 = base64.b64encode(resolved.read_bytes()).decode("ascii")
        src = f"data:image/{ext};base64,{b64}"
    else:
        src = resolved  # URL
    st.markdown(
        f'<div class="illust-fixed" style="height:{height}px;">'
        f'<img src="{src}" style="max-height:100%; max-width:100%; object-fit:contain;" />'
        f'</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)
