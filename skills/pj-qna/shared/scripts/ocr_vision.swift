// macOS Vision OCR — 이미지 경로들을 받아 같은 이름의 .txt로 저장한다 (한국어·영어). extract_target.py가 처음 쓸 때 컴파일해 캐시한다
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        FileHandle.standardError.write("읽기 실패: \(path)\n".data(using: .utf8)!)
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["ko-KR", "en-US"]
    req.usesLanguageCorrection = true
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    // 위에서 아래, 왼쪽에서 오른쪽 순서로 줄을 모은다
    let obs = (req.results ?? []).sorted {
        abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.01
            ? $0.boundingBox.midY > $1.boundingBox.midY
            : $0.boundingBox.minX < $1.boundingBox.minX
    }
    let text = obs.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    let out = (path as NSString).deletingPathExtension + ".txt"
    try? text.write(toFile: out, atomically: true, encoding: .utf8)
    print("\(path): \(obs.count)줄")
}
