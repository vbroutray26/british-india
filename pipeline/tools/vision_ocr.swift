// Apple Vision OCR for page scans (DP-01 alternative engine, D-24).
// Usage: vision_ocr [--correct] <image> [<image> ...]   (--correct turns on Vision's language correction)
// Prints one JSON object per image: {"file", "w", "h", "lines": [{"t", "conf", "x0", "y0", "x1", "y1"}]}
// Coordinates are pixels with the origin at the top left.
import Foundation
import Vision
import AppKit

func ocr(_ path: String, correct: Bool) -> [String: Any] {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        return ["file": path, "error": "cannot read image"]
    }
    let w = Double(cg.width), h = Double(cg.height)
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = correct
    req.recognitionLanguages = ["en-US"]
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try? handler.perform([req])
    var lines: [[String: Any]] = []
    for obs in req.results ?? [] {
        guard let top = obs.topCandidates(1).first else { continue }
        let b = obs.boundingBox  // normalised, origin bottom-left
        lines.append(["t": top.string, "conf": Double(top.confidence),
                      "x0": Int(b.minX * w), "y0": Int((1 - b.maxY) * h),
                      "x1": Int(b.maxX * w), "y1": Int((1 - b.minY) * h)])
    }
    return ["file": path, "w": Int(w), "h": Int(h), "lines": lines]
}

let args = Array(CommandLine.arguments.dropFirst())
let correct = args.contains("--correct")
for path in args where path != "--correct" {
    let data = try! JSONSerialization.data(withJSONObject: ocr(path, correct: correct), options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
}
