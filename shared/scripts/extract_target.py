#!/usr/bin/env python3
"""채점 대상 파일에서 텍스트를 뽑아 <런>/target/<이름>.txt로 저장한다.

합산은 이 원문과 인용을 대조한다. 발표자료 PDF는 슬라이드가 이미지인 경우가 많아
pdftotext만 쓰면 빈 쪽이 나오고 인용 대조가 사실상 꺼진다 — 글자가 거의 없는 쪽은 OCR한다.

- PDF: PyMuPDF → pdftotext/pdftoppm → pypdf(이미지 렌더 없음) 순으로 쓸 수 있는 것을 고른다
- OCR: macOS Vision(내장) / Windows.Media.Ocr(내장, PowerShell) / tesseract(kor+eng)
- OCR 도구가 없으면 그 쪽을 <런>/target_images/에 PNG로 남기고, 에이전트가 이미지로 읽는다
- PPTX·DOCX는 표준 라이브러리(zip+XML)로 읽는다

사용: extract_target.py <런 폴더> <파일...> [--pages 27-47] [--ocr auto|vision|windows|tesseract|none]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import InputError, run_cli  # noqa: E402

# 공백을 뺀 글자가 이보다 적으면 이미지 쪽으로 본다 — 쪽 번호·머리글만 있는 슬라이드를 걸러낸다
TEXT_MIN_CHARS = 20
RENDER_DPI = 150
PLAIN_SUFFIXES = {".md", ".txt", ".markdown", ".csv", ".json", ".yaml", ".yml", ".html"}


def parse_pages(spec, total: int) -> list:
    if not spec:
        return list(range(1, total + 1))
    pages = []
    for part in str(spec).split(","):
        m = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", part)
        if not m:
            raise InputError(f"쪽 범위 형식 오류: '{part}' (예: 27-47,50)")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if a < 1 or b > total or a > b:
            raise InputError(f"쪽 범위 {a}-{b}가 문서 쪽수(1-{total}) 밖이거나 거꾸로다")
        pages.extend(range(a, b + 1))
    return pages


def needs_ocr(text: str) -> bool:
    return len(re.sub(r"\s", "", text or "")) < TEXT_MIN_CHARS


# ---------- PDF 백엔드 ----------

class PyMuPDFBackend:
    name = "pymupdf"

    def __init__(self, mod):
        self.mod = mod
        self._docs = {}

    def _doc(self, path):
        if path not in self._docs:
            self._docs[path] = self.mod.open(str(path))
        return self._docs[path]

    def page_count(self, path):
        return self._doc(path).page_count

    def page_text(self, path, n):
        return self._doc(path)[n - 1].get_text()

    def render(self, path, n, out):
        self._doc(path)[n - 1].get_pixmap(dpi=RENDER_DPI).save(str(out))
        return True


class PopplerBackend:
    name = "poppler"

    def page_count(self, path):
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        if not m:
            raise InputError(f"PDF를 열 수 없음: {path}")
        return int(m.group(1))

    def page_text(self, path, n):
        return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(path), "-"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

    def render(self, path, n, out):
        prefix = out.with_suffix("")
        subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-r", str(RENDER_DPI), "-png",
                        "-singlefile", str(path), str(prefix)], capture_output=True)
        return out.is_file()


class PypdfBackend:
    name = "pypdf"

    def __init__(self, mod):
        self.mod = mod

    def page_count(self, path):
        return len(self.mod.PdfReader(str(path)).pages)

    def page_text(self, path, n):
        return self.mod.PdfReader(str(path)).pages[n - 1].extract_text() or ""

    def render(self, path, n, out):
        return False  # pypdf는 쪽을 그림으로 그리지 못한다


def pick_pdf_backend():
    for modname in ("pymupdf", "fitz"):
        try:
            return PyMuPDFBackend(__import__(modname))
        except ImportError:
            continue
    if shutil.which("pdftotext") and shutil.which("pdfinfo"):
        return PopplerBackend()
    try:
        return PypdfBackend(__import__("pypdf"))
    except ImportError:
        pass
    raise InputError("PDF를 읽을 도구가 없습니다: python3 -m pip install pymupdf (Windows·macOS·Linux 공통)")


# ---------- OCR 엔진: 이미지 목록 → {이미지: 글자} ----------

VISION_SRC = Path(__file__).resolve().parent / "ocr_vision.swift"


def _vision_binary():
    """Swift 도우미를 처음 한 번 컴파일해 캐시한다. 소스가 바뀌면 해시가 바뀌어 다시 만든다."""
    if platform.system() != "Darwin" or not shutil.which("swiftc") or not VISION_SRC.is_file():
        return None
    digest = hashlib.sha256(VISION_SRC.read_bytes()).hexdigest()[:12]
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "pro-judge"
    binary = cache / f"ocr-vision-{digest}"
    if not binary.is_file():
        cache.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["swiftc", "-O", str(VISION_SRC), "-o", str(binary)], capture_output=True, text=True)
        if r.returncode != 0:
            return None
    return binary


def vision_ocr(binary):
    def run(images):
        subprocess.run([str(binary), *map(str, images)], capture_output=True)
        result = {}
        for img in images:
            txt = img.with_suffix(".txt")
            result[img] = txt.read_text(encoding="utf-8") if txt.is_file() else ""
            if txt.is_file():
                txt.unlink()
        return result
    run.name = "vision"
    return run


# Windows 10 이상에 들어 있는 OCR. 한국어 언어 팩이 없으면 사용자 프로필 언어로 읽는다
WINDOWS_OCR_PS1 = r"""
param([string]$Path)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics,ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $null = $task.Wait(-1); $task.Result }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$lang = New-Object Windows.Globalization.Language 'ko'
if ([Windows.Media.Ocr.OcrEngine]::IsLanguageSupported($lang)) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang) }
else { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$result.Lines | ForEach-Object { $_.Text }
"""


def _windows_script() -> Path:
    path = Path(tempfile.gettempdir()) / "pro-judge-ocr.ps1"
    path.write_text(WINDOWS_OCR_PS1, encoding="utf-8-sig")  # BOM이 있어야 PowerShell 5.1이 UTF-8로 읽는다
    return path


def windows_ocr_command(image: Path, script: Path = Path("pro-judge-ocr.ps1")) -> list:
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(image)]


def windows_ocr():
    script = _windows_script()

    def run(images):
        return {img: subprocess.run(windows_ocr_command(img, script), capture_output=True,
                                    text=True, encoding="utf-8", errors="replace").stdout
                for img in images}
    run.name = "windows"
    return run


def tesseract_ocr():
    langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout.split()
    lang = "+".join(l for l in ("kor", "eng") if l in langs) or "eng"

    def run(images):
        return {img: subprocess.run(["tesseract", str(img), "-", "-l", lang], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace").stdout
                for img in images}
    run.name = f"tesseract({lang})"
    return run


def pick_ocr(choice: str = "auto"):
    if choice == "none":
        return None
    system = platform.system()
    if choice in ("auto", "vision") and system == "Darwin":
        binary = _vision_binary()
        if binary:
            return vision_ocr(binary)
    if choice in ("auto", "windows") and system == "Windows" and shutil.which("powershell"):
        return windows_ocr()
    if choice in ("auto", "tesseract") and shutil.which("tesseract"):
        return tesseract_ocr()
    if choice != "auto":
        raise InputError(f"OCR 엔진 '{choice}'을(를) 이 환경에서 쓸 수 없습니다")
    return None


# ---------- 형식별 추출 ----------

def extract_pdf(path: Path, pages_spec, backend, ocr, img_dir: Path):
    """쪽마다 글자를 뽑고, 글자가 거의 없는 쪽은 OCR한다. OCR이 안 되면 쪽 이미지를 남긴다."""
    stem = path.stem
    pages = parse_pages(pages_spec, backend.page_count(path))
    stats = {"pages": len(pages), "text": 0, "ocr": 0, "image": []}
    chunks, pending = {}, []
    for n in pages:
        text = backend.page_text(path, n)
        if not needs_ocr(text):
            chunks[n] = ("text", text)
            stats["text"] += 1
            continue
        img_dir.mkdir(parents=True, exist_ok=True)
        png = img_dir / f"{stem}-p{n:03d}.png"
        if backend.render(path, n, png):
            pending.append((n, png))
        else:
            chunks[n] = ("unreadable", text)
    results = ocr([png for _, png in pending]) if (ocr and pending) else {}
    for n, png in pending:
        got = results.get(png, "")
        # 슬라이드 글자는 짧다 — OCR 결과는 몇 글자라도 있으면 받는다
        if re.sub(r"\s", "", got):
            chunks[n] = ("ocr", got)
            stats["ocr"] += 1
            png.unlink()
        else:
            chunks[n] = (f"image: {png}", got)  # 에이전트가 이 이미지를 직접 읽는다
            stats["image"].append(png)
    body = "\n".join(f"--- {stem} p{n} [{kind}] ---\n{text.strip()}" for n, (kind, text) in sorted(chunks.items()))
    return body + "\n", stats


def _xml_text(data: bytes, para_tag: str, text_tag: str) -> list:
    root = ET.fromstring(data)
    paras = []
    for p in root.iter():
        if p.tag.endswith("}" + para_tag):
            line = "".join(t.text or "" for t in p.iter() if t.tag.endswith("}" + text_tag))
            if line.strip():
                paras.append(line)
    return paras


def extract_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        slides.sort(key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
        out = []
        for n in slides:
            num = re.search(r"(\d+)\.xml$", n).group(1)
            out.append(f"--- {path.stem} slide{num} ---\n" + "\n".join(_xml_text(z.read(n), "p", "t")))
    return "\n".join(out) + "\n"


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        return "\n".join(_xml_text(z.read("word/document.xml"), "p", "t"))


def _unique(target: Path, stem: str) -> Path:
    out, i = target / f"{stem}.txt", 2
    while out.exists():
        out, i = target / f"{stem}-{i}.txt", i + 1
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="채점 대상 → <런>/target/*.txt (이미지 쪽은 OCR)")
    ap.add_argument("run_dir")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--pages", help="PDF 쪽 범위 (예: 27-47,50). 여러 파일이면 모두에 적용")
    ap.add_argument("--ocr", default="auto", choices=["auto", "vision", "windows", "tesseract", "none"])
    args = ap.parse_args(argv)

    files = [Path(f) for f in args.files]
    for f in files:
        if not f.is_file():
            raise InputError(f"파일 없음: {f}")
        if f.suffix.lower() not in PLAIN_SUFFIXES | {".pdf", ".pptx", ".docx"}:
            raise InputError(f"지원하지 않는 형식: {f.name} — PDF로 저장하거나(hwp·ppt·doc) 화면을 캡처해 이미지로 읽힌다")
    run_dir = Path(args.run_dir)
    target, img_dir = run_dir / "target", run_dir / "target_images"
    target.mkdir(parents=True, exist_ok=True)

    backend = ocr = None
    images = []
    for f in files:
        suffix = f.suffix.lower()
        if suffix == ".pdf":
            if backend is None:
                backend = pick_pdf_backend()
                ocr = pick_ocr(args.ocr)
            text, st = extract_pdf(f, args.pages, backend, ocr, img_dir)
            images += st["image"]
            how = f"PDF {st['pages']}쪽: 글자 {st['text']} · OCR {st['ocr']}({getattr(ocr, 'name', '없음')}) · 이미지 {len(st['image'])}"
        elif suffix == ".pptx":
            text, how = extract_pptx(f), "PPTX 슬라이드 글자 (슬라이드 속 그림 글자는 PDF로 내보내 OCR)"
        elif suffix == ".docx":
            text, how = extract_docx(f), "DOCX 문단"
        else:
            text, how = f.read_text(encoding="utf-8", errors="replace"), "텍스트 그대로"
        out = _unique(target, f.stem)
        out.write_text(text, encoding="utf-8")
        print(f"{out}  ← {f.name} ({how})")
    if images:
        print(f"이미지로 읽을 쪽 {len(images)}개 (OCR 도구 없음 또는 인식 실패) — 에이전트가 직접 열어 읽고 "
              f"읽은 글을 target/에 덧붙인다:")
        for img in images:
            print(f"  {img}")
    return 0


if __name__ == "__main__":
    run_cli(main)
