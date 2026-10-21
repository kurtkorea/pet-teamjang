"""라벨 형식, 분할, 압축 해제 단위 테스트."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from dog_detect.dataset import (
    autolabel_pairs,
    find_label,
    list_images,
    prepare_dataset,
    safe_extract,
)
from dog_detect.sampling import frame_stem, frame_step, should_infer
from dog_detect.yolo_fmt import (
    assign_split,
    format_yolo_line,
    remap_label_text,
    write_yolo11_annotation_zip,
)


class SamplingTest(unittest.TestCase):
    def test_frame_step(self) -> None:
        self.assertEqual(frame_step(30, 2), 15)
        self.assertEqual(frame_step(0, 1), 30)
        self.assertEqual(frame_step(29.97, 1), 30)
        with self.assertRaises(ValueError):
            frame_step(30, 0)

    def test_should_infer(self) -> None:
        self.assertTrue(should_infer(0, 0, 0, 5))
        self.assertTrue(should_infer(0, None, 2.5, 5))
        self.assertFalse(should_infer(1, 1.0, 2.5, 5))
        self.assertTrue(should_infer(5, 1.0, 2.5, 5))
        self.assertFalse(should_infer(9, 1.0, 2.5, 0))
        self.assertTrue(should_infer(0, 3.0, 2.5, 5))

    def test_frame_stem_depends_on_path(self) -> None:
        first = frame_stem(Path("D:/videos/a.mp4"), 1)
        second = frame_stem(Path("D:/other/a.mp4"), 1)
        again = frame_stem(Path("D:/videos/a.mp4"), 1)
        self.assertEqual(first, again)
        self.assertNotEqual(first, second)
        self.assertTrue(first.endswith("_f000001"))


class YoloFormatTest(unittest.TestCase):
    def test_clamp(self) -> None:
        self.assertEqual(
            format_yolo_line(0, -0.2, 1.2, 0.5, 0.25),
            "0 0.000000 1.000000 0.500000 0.250000",
        )

    def test_remap(self) -> None:
        text = remap_label_text("0 0.1 0.2 0.3 0.4\n1 0.2 0.2 0.2 0.2\n", 2)
        self.assertEqual(text, "2 0.1 0.2 0.3 0.4\n")

    def test_split_is_stable_and_covers_every_name(self) -> None:
        names = [f"{index}.jpg" for index in range(50)]
        train, val = assign_split(names, 0.2, 7)
        self.assertEqual(set(train) | set(val), set(names))
        self.assertFalse(set(train) & set(val))
        self.assertEqual(assign_split(names, 0.2, 7), (train, val))
        self.assertTrue(train and val)
        only_train, only_val = assign_split(["only.jpg"], 0.2, 1)
        self.assertEqual(only_train, ["only.jpg"])
        self.assertEqual(only_val, ["only.jpg"])

    def test_annotation_zip_uses_cvat_label_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "dog_f000001.jpg"
            image.write_bytes(b"img")
            labels = root / "labels"
            labels.mkdir()
            (labels / "dog_f000001.txt").write_text(
                "0 0.100000 0.200000 0.300000 0.400000\n",
                encoding="utf-8",
            )
            dest = root / "ann.zip"
            write_yolo11_annotation_zip([image], labels, dest, ["person", "dog"], 1)
            with zipfile.ZipFile(dest) as archive:
                names = archive.read("obj.names").decode().splitlines()
                body = archive.read("obj_train_data/dog_f000001.txt").decode()
                listing = archive.read("train.txt").decode()
            self.assertEqual(names[1], "dog")
            self.assertTrue(body.startswith("1 "))
            self.assertIn("obj_train_data/dog_f000001.jpg", listing)


class DatasetTest(unittest.TestCase):
    def test_extract_rejects_parent_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "ok.zip"
            with zipfile.ZipFile(good, "w") as archive:
                archive.writestr("images/train/a.jpg", b"jpeg")
                archive.writestr("labels/train/a.txt", "0 0.5 0.5 0.2 0.2\n")
            out = root / "out"
            safe_extract(good, out)
            image = out / "images" / "train" / "a.jpg"
            self.assertEqual(image.read_bytes(), b"jpeg")
            label = find_label(image)
            self.assertIsNotNone(label)
            assert label is not None
            self.assertTrue(label.is_file())

            bad = root / "bad.zip"
            with zipfile.ZipFile(bad, "w") as archive:
                archive.writestr("../evil.txt", "x")
            with self.assertRaises(RuntimeError):
                safe_extract(bad, root / "badout")
            self.assertFalse((root / "evil.txt").exists())

    def test_prepare_dataset_writes_ultralytics_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            images = root / "images"
            labels = root / "labels"
            images.mkdir()
            labels.mkdir()
            for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
                (images / name).write_bytes(b"img")
                (labels / f"{Path(name).stem}.txt").write_text(
                    "0 0.5 0.5 0.2 0.2\n",
                    encoding="utf-8",
                )
            dest = root / "dataset"
            yaml_path = prepare_dataset(autolabel_pairs(root), dest, 0.25, 42, "dog")
            path_line = next(line for line in yaml_path.read_text(encoding="utf-8").splitlines() if line.startswith("path:"))
            self.assertNotIn("\\", path_line)
            self.assertIn("0: dog", yaml_path.read_text(encoding="utf-8"))
            train = list_images(dest / "images" / "train")
            val = list_images(dest / "images" / "val")
            self.assertEqual(len(train) + len(val), 4)
            self.assertTrue(train and val)
            self.assertFalse({path.name for path in train} & {path.name for path in val})


class ConfigTest(unittest.TestCase):
    def test_load_config(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("pyyaml 없음")
        from dog_detect.config import default_config_path, load_config

        cfg = load_config(default_config_path())
        self.assertEqual(cfg.detect.class_name, "dog")
        self.assertEqual(cfg.detect.model, "runs/dog-yolo11n/weights/best.pt")
        self.assertEqual(cfg.live.source, "rtsp://techfinai.iptime.org/stream1")
        self.assertEqual(cfg.train.batch, 16)
        self.assertEqual(cfg.cvat.label, "dog")
        self.assertEqual(cfg.paths.videos.name, "videos")


if __name__ == "__main__":
    unittest.main()
