"""채점 대상 파일 → <런>/target/*.txt 추출. PDF 백엔드·OCR 엔진은 가짜로 바꿔 끼워 OS와 무관하게 검사한다."""
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import pytest

from _common import InputError
import extract_target as et


class FakePdf:
    """쪽마다 정해 둔 글자를 돌려주는 PDF 백엔드. render는 빈 PNG를 쓴다."""
    name = "fake"

    def __init__(self, pages, can_render=True):
        self.pages = pages
        self.can_render = can_render

    def page_count(self, path):
        return len(self.pages)

    def page_text(self, path, n):
        return self.pages[n - 1]

    def render(self, path, n, out):
        if not self.can_render:
            return False
        out.write_bytes(b"png")
        return True


def fake_ocr(text_by_page):
    def run(images):
        return {img: text_by_page.get(img.stem.rsplit("-p", 1)[1].lstrip("0"), "") for img in images}
    run.name = "fake-ocr"
    return run


def test_parse_pages():
    assert et.parse_pages(None, 5) == [1, 2, 3, 4, 5]
    assert et.parse_pages("2-3,5", 5) == [2, 3, 5]
    for bad in ("0-2", "4-9", "3-1", "a"):
        with pytest.raises(InputError):
            et.parse_pages(bad, 5)


def test_text_pages_skip_ocr(tmp_path):
    pdf = FakePdf(["첫 쪽 본문이 충분히 길게 들어 있다 스무 글자를 넘긴다", "둘째 쪽 본문도 충분히 길게 들어 있다 스무 글자를 넘긴다"])
    text, stats = et.extract_pdf(tmp_path / "a.pdf", None, pdf, None, tmp_path / "img")
    assert "첫 쪽 본문" in text and "--- a p2 [text] ---" in text
    assert stats == {"pages": 2, "text": 2, "ocr": 0, "image": [], "visual": []}


def test_image_page_goes_to_ocr(tmp_path):
    # 슬라이드가 이미지인 쪽은 pdftotext가 쪽 번호 정도만 낸다 — OCR로 채운다
    pdf = FakePdf(["본문이 충분히 길게 들어 있는 쪽이다 열두자 이상으로 더 길게 쓴 본문", "27"])
    text, stats = et.extract_pdf(tmp_path / "deck.pdf", None, pdf, fake_ocr({"2": "모두의운동장 시연 화면"}), tmp_path / "img")
    png = tmp_path / "img" / "deck-p002.png"
    assert f"--- deck p2 [ocr, image: {png}] ---\n모두의운동장 시연 화면" in text
    assert stats["ocr"] == 1 and stats["image"] == []
    # 앱 화면·도표·색 대비는 글자로 안 남는다 — 그림 확인용으로 이미지를 보관한다
    assert stats["visual"] == [png] and png.is_file()


def test_no_ocr_keeps_image_for_agent(tmp_path):
    # OCR 도구가 없으면(Windows 기본 등) 쪽 이미지를 남겨 에이전트가 이미지로 읽게 한다
    pdf = FakePdf(["", "본문이 충분히 길게 들어 있는 쪽이다 열두자 이상으로 더 길게 쓴 본문"])
    text, stats = et.extract_pdf(tmp_path / "deck.pdf", "1", pdf, None, tmp_path / "img")
    png = tmp_path / "img" / "deck-p001.png"
    assert stats["image"] == [png] and png.is_file()
    assert f"[image: {png}]" in text


def test_no_renderer_marks_unreadable(tmp_path):
    pdf = FakePdf([""], can_render=False)
    text, stats = et.extract_pdf(tmp_path / "deck.pdf", None, pdf, None, tmp_path / "img")
    assert "[unreadable]" in text and stats["image"] == []


def _zip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for name, body in files.items():
            z.writestr(name, body)


A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'


def test_pptx_slides_in_numeric_order(tmp_path):
    p = tmp_path / "deck.pptx"
    slide = lambda t: f'<p:sld {A} xmlns:p="x"><a:p><a:r><a:t>{t}</a:t></a:r><a:r><a:t> 끝</a:t></a:r></a:p></p:sld>'
    _zip(p, {"ppt/slides/slide10.xml": slide("열"), "ppt/slides/slide2.xml": slide("둘")})
    text = et.extract_pptx(p)
    assert text.index("--- deck slide2 ---") < text.index("--- deck slide10 ---")
    assert "둘 끝" in text


def test_docx_paragraphs(tmp_path):
    p = tmp_path / "plan.docx"
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    _zip(p, {"word/document.xml": f'<w:document {w}><w:body><w:p><w:r><w:t>첫 문단</w:t></w:r></w:p>'
                                   f'<w:p><w:r><w:t>둘째</w:t></w:r></w:p></w:body></w:document>'})
    assert et.extract_docx(p) == "첫 문단\n둘째"


def test_cli_writes_target_and_lists_images(tmp_path, capsys, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    (tmp_path / "note.md").write_text("발표 메모", encoding="utf-8")
    (tmp_path / "deck.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr(et, "pick_pdf_backend", lambda: FakePdf(["", "본문이 충분히 길게 들어 있는 쪽이다 열두자 이상으로 더 길게 쓴 본문"]))
    monkeypatch.setattr(et, "pick_ocr", lambda choice: None)
    assert et.main([str(run), str(tmp_path / "note.md"), str(tmp_path / "deck.pdf")]) == 0
    assert (run / "target" / "note.txt").read_text(encoding="utf-8") == "발표 메모"
    assert (run / "target_images" / "deck-p001.png").is_file()
    out = capsys.readouterr().out
    assert "이미지로 읽을 쪽" in out and "deck-p001.png" in out


def test_same_stem_does_not_overwrite(tmp_path):
    run = tmp_path / "run"
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "slides.md").write_text("A", encoding="utf-8")
    (tmp_path / "b" / "slides.md").write_text("B", encoding="utf-8")
    et.main([str(run), str(tmp_path / "a" / "slides.md"), str(tmp_path / "b" / "slides.md")])
    assert sorted(p.name for p in (run / "target").iterdir()) == ["slides-2.txt", "slides.txt"]


def test_unsupported_and_missing(tmp_path):
    (tmp_path / "x.hwp").write_bytes(b"x")
    with pytest.raises(InputError, match="hwp"):
        et.main([str(tmp_path / "run"), str(tmp_path / "x.hwp")])
    with pytest.raises(InputError, match="파일 없음"):
        et.main([str(tmp_path / "run"), str(tmp_path / "없음.pdf")])


def test_windows_ocr_command_is_built_in_powershell(tmp_path):
    # Windows는 내장 Windows.Media.Ocr을 PowerShell로 부른다 — 설치 없이 동작해야 한다
    cmd = et.windows_ocr_command(tmp_path / "p.png")
    assert cmd[0] == "powershell" and "-File" in cmd and str(tmp_path / "p.png") in cmd
    assert "Windows.Media.Ocr" in et.WINDOWS_OCR_PS1


def test_pick_ocr_none_when_disabled():
    assert et.pick_ocr("none") is None


class FakeRun:
    """subprocess.run 대역. pdfinfo·pdftotext 호출을 기록하고 정해 둔 출력을 돌려준다."""

    def __init__(self, pages, whole_ok=True):
        self.pages, self.whole_ok, self.calls = pages, whole_ok, []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        if cmd[0] == "pdfinfo":
            out, code = f"Pages:          {len(self.pages)}\n", 0
        elif "-f" in cmd:
            out, code = self.pages[int(cmd[cmd.index("-f") + 1]) - 1] + "\f", 0
        else:
            out = "".join(p + "\f" for p in self.pages) if self.whole_ok else "깨진 출력"
            code = 0 if self.whole_ok else 1
        return subprocess.CompletedProcess(cmd, code, stdout=out, stderr="")


def test_poppler_extracts_whole_document_once(tmp_path, monkeypatch):
    # 쪽마다 pdftotext를 띄우지 않는다 — 100쪽 실측 1.57초 → 0.02초
    fake = FakeRun(["첫 쪽", "둘째 쪽", "셋째 쪽"])
    monkeypatch.setattr(et.subprocess, "run", fake)
    b, pdf = et.PopplerBackend(), tmp_path / "a.pdf"
    assert [b.page_text(pdf, n) for n in (1, 2, 3)] == ["첫 쪽\f", "둘째 쪽\f", "셋째 쪽\f"]
    assert sum(c[0] == "pdftotext" for c in fake.calls) == 1


def test_poppler_falls_back_to_per_page_when_whole_fails(tmp_path, monkeypatch):
    fake = FakeRun(["첫 쪽", "둘째 쪽"], whole_ok=False)
    monkeypatch.setattr(et.subprocess, "run", fake)
    b, pdf = et.PopplerBackend(), tmp_path / "a.pdf"
    assert b.page_text(pdf, 2) == "둘째 쪽\f"
    assert ["-f", "2"] == [c for c in fake.calls if "-f" in c][0][1:3]


@pytest.mark.skipif(not (shutil.which("pdftotext") and shutil.which("pdfinfo")), reason="poppler 없음")
def test_poppler_whole_matches_per_page_on_real_pdf(tmp_path):
    # 한 번에 뽑아 나눈 글자가 쪽별 호출 결과와 한 글자도 다르지 않아야 한다
    fitz = pytest.importorskip("pymupdf")
    pdf = tmp_path / "real.pdf"
    doc = fitz.open()
    for i in range(5):
        doc.new_page().insert_text((72, 72), f"page {i + 1} body text long enough", fontsize=11)
    doc.new_page()  # 빈 쪽도 쪽 수가 어긋나지 않아야 한다
    doc.save(str(pdf))
    b = et.PopplerBackend()
    per_page = [subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(pdf), "-"],
                               capture_output=True, text=True).stdout for n in range(1, 7)]
    assert [b.page_text(pdf, n) for n in range(1, 7)] == per_page
    assert b._pages[pdf] is not None  # 실제로 한 번에 뽑는 경로를 탔다


def test_pypdf_reader_opened_once(tmp_path):
    opened = []

    class Page:
        def __init__(self, n):
            self.n = n

        def extract_text(self):
            return f"쪽 {self.n}"

    class Reader:
        def __init__(self, path):
            opened.append(path)
            self.pages = [Page(n) for n in (1, 2, 3)]

    b = et.PypdfBackend(type("pypdf", (), {"PdfReader": Reader}))
    pdf = tmp_path / "a.pdf"
    assert b.page_count(pdf) == 3
    assert [b.page_text(pdf, n) for n in (1, 2, 3)] == ["쪽 1", "쪽 2", "쪽 3"]
    assert len(opened) == 1


def test_ocr_each_runs_in_parallel_and_keeps_mapping(tmp_path, monkeypatch):
    # 결과는 이미지별로 그대로 짝지어져야 하고, 장당 시간이 쌓이지 않아야 한다
    images = [tmp_path / f"p{n}.png" for n in range(4)]
    started, ended, envs = [], [], []

    def fake_run(cmd, **kw):
        started.append(time.monotonic())
        envs.append(kw.get("env"))
        time.sleep(0.2)
        ended.append(time.monotonic())
        return subprocess.CompletedProcess(cmd, 0, stdout=f"글자 {Path(cmd[1]).stem}", stderr="")

    monkeypatch.setattr(et.subprocess, "run", fake_run)
    monkeypatch.setattr(et, "OCR_WORKERS", 4)
    got = et._ocr_each(lambda img: ["ocr", str(img)], images, {"OMP_THREAD_LIMIT": "1"})
    assert got == {img: f"글자 {img.stem}" for img in images}
    assert max(started) < min(ended)  # 넷 모두 하나가 끝나기 전에 시작했다
    assert envs == [{"OMP_THREAD_LIMIT": "1"}] * 4


class BrokenPage(FakePdf):
    """특정 쪽에서 백엔드가 예외를 던진다 (실측: 색 공간이 깨진 PDF 쪽에서 PyMuPDF SystemError)."""
    def page_text(self, path, n):
        if n == 2:
            raise SystemError("unknown colorspace")
        return super().page_text(path, n)

    def render(self, path, n, out):
        if n == 2:
            raise SystemError("unknown colorspace")
        return super().render(path, n, out)


def test_broken_page_does_not_stop_extraction(tmp_path):
    long = "본문이 충분히 길게 들어 있는 쪽이다 스무 글자를 넘긴다"
    pdf = BrokenPage([long, "", long])
    text, stats = et.extract_pdf(tmp_path / "d.pdf", None, pdf, None, tmp_path / "img")
    assert "--- d p2 [unreadable] ---" in text and "--- d p3 [text] ---" in text


def test_broken_page_falls_back_to_second_backend(tmp_path):
    long = "본문이 충분히 길게 들어 있는 쪽이다 스무 글자를 넘긴다"
    backend = et.FallbackPdf(BrokenPage([long, "", long]), FakePdf([long, "둘째 쪽은 다른 도구로 읽힌다 스무 글자를 넘긴다", long]))
    text, _ = et.extract_pdf(tmp_path / "d.pdf", None, backend, None, tmp_path / "img")
    assert "--- d p2 [text] ---\n둘째 쪽은 다른 도구로" in text
