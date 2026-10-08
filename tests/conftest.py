import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# 스크립트는 패키지가 아니라 단독 실행 파일이라 경로를 직접 넣는다
sys.path.insert(0, str(ROOT / "shared" / "scripts"))
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def contest_dir(tmp_path):
    """정상 대회 폴더 사본. 테스트가 마음대로 고쳐도 원본은 안전하다."""
    dst = tmp_path / "contest"
    shutil.copytree(FIXTURES / "contest_ok", dst)
    return dst
