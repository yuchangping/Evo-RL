#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def load_font(size: int):
    candidates = [
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/usr/local/share/fonts/DejaVuSans.ttf'),
    ]
    for c in candidates:
        if c.exists():
            return ImageFont.truetype(str(c), size=size)
    return ImageFont.load_default()


def extract_frame_by_ratio(video_path: Path, ratio: float) -> Image.Image:
    container = av.open(str(video_path))
    stream = container.streams.video[0]
    total = int(stream.frames)
    if total <= 0:
        # fallback for codecs missing frame count
        frames = [f for f in container.decode(stream)]
        if not frames:
            raise RuntimeError(f'No frames decoded: {video_path}')
        idx = min(max(int(round(ratio * (len(frames) - 1))), 0), len(frames) - 1)
        img = frames[idx].to_image().convert('RGB')
        container.close()
        return img

    target = min(max(int(round(ratio * (total - 1))), 0), total - 1)
    nearest = None
    for i, frame in enumerate(container.decode(stream)):
        if i >= target:
            nearest = frame
            break
    if nearest is None:
        raise RuntimeError(f'Could not decode target frame from: {video_path}')
    img = nearest.to_image().convert('RGB')
    container.close()
    return img


def make_contact_sheet(video_path: Path, out_dir: Path, ratios: list[float]) -> Path:
    stem = video_path.stem
    key_dir = out_dir / 'keyframes' / stem
    ensure_dir(key_dir)

    frames = []
    labels = []
    for r in ratios:
        img = extract_frame_by_ratio(video_path, r)
        frames.append(img)
        labels.append(f'{int(round(r * 100)):02d}%')

    w, h = frames[0].size
    cols = len(frames)
    title_h = 56
    label_h = 32
    pad = 14
    canvas_w = cols * w + (cols + 1) * pad
    canvas_h = title_h + h + label_h + 2 * pad
    canvas = Image.new('RGB', (canvas_w, canvas_h), (16, 20, 24))
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(26)
    label_font = load_font(22)
    draw.text((pad, 10), stem, fill=(235, 240, 245), font=title_font)

    for i, (img, lb) in enumerate(zip(frames, labels, strict=True)):
        x = pad + i * (w + pad)
        y = title_h
        canvas.paste(img, (x, y))
        draw.rectangle((x, y + h + 3, x + 90, y + h + 30), fill=(0, 0, 0))
        draw.text((x + 8, y + h + 6), lb, fill=(255, 220, 120), font=label_font)

        frame_path = key_dir / f'frame_{lb}.png'
        img.save(frame_path)

    sheet_dir = out_dir / 'contact_sheets'
    ensure_dir(sheet_dir)
    sheet_path = sheet_dir / f'{stem}_contact_sheet.png'
    canvas.save(sheet_path)
    return sheet_path


def main() -> None:
    parser = argparse.ArgumentParser(description='Export keyframes and contact sheets from paper videos.')
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--ratios', type=str, default='0.10,0.25,0.40,0.55,0.70,0.85')
    args = parser.parse_args()

    ratios = [float(x.strip()) for x in args.ratios.split(',') if x.strip()]
    ensure_dir(args.output_dir)

    videos = sorted([p for p in args.input_dir.glob('*.mp4')])
    if not videos:
        raise FileNotFoundError(f'No mp4 files found under {args.input_dir}')

    sheets = []
    for v in videos:
        sheet = make_contact_sheet(v, args.output_dir, ratios)
        sheets.append(sheet)
        print(f'[done] {sheet}')

    print(f'[summary] videos={len(videos)} sheets={len(sheets)} output={args.output_dir}')


if __name__ == '__main__':
    main()
