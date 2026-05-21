from __future__ import annotations

import csv
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from mvp_image_workflow.batch import ProductRow
from mvp_image_workflow.cli import main as cli_main
from mvp_image_workflow.generator import generate_product_package
from mvp_image_workflow.io_csv import read_products_csv
from mvp_image_workflow.validator import validate_product_package
from mvp_image_workflow.util import ValidationError


class TestMvpImageWorkflow(unittest.TestCase):
    def test_generate_and_validate_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "in.csv"

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "product_id",
                        "product_name_en",
                        "style_pack",
                        "output_set",
                        "units",
                        "dimensions_l",
                        "dimensions_w",
                        "dimensions_h",
                        "spec_1",
                        "spec_2",
                        "spec_3",
                        "howto_title",
                        "step_1",
                        "step_2",
                        "step_3",
                    ]
                )
                w.writerow(
                    [
                        "SKU123",
                        "Stainless Steel Insulated Tumbler",
                        "minimal_white",
                        "minimum",
                        "cm",
                        "20",
                        "8",
                        "8",
                        "Capacity: 500 ml",
                        "Double-wall insulation",
                        "Leak-proof lid",
                        "How to Use",
                        "Fill with your drink",
                        "Close the lid firmly",
                        "Enjoy hot or cold beverages",
                    ]
                )

            products = read_products_csv(csv_path)
            self.assertEqual(len(products), 1)
            product_dir = generate_product_package(products[0], root / "out", batch_id="B1")

            validate_product_package(product_dir, require_images=False)

            # Require images: should fail until we create empty placeholders.
            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

            manifest = (product_dir / "manifest.json").read_text(encoding="utf-8")
            self.assertIn("expected_outputs", manifest)

            import json

            expected = json.loads(manifest)["expected_outputs"]
            for category, files in expected.items():
                for fname in files:
                    (product_dir / category / fname).write_bytes(b"")

            validate_product_package(product_dir, require_images=True)

    def test_batch_id_rejects_unsafe_characters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "in.csv"

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "product_id",
                        "product_name_en",
                        "style_pack",
                        "output_set",
                        "units",
                        "spec_1",
                        "spec_2",
                        "spec_3",
                        "howto_title",
                        "step_1",
                        "step_2",
                        "step_3",
                    ]
                )
                w.writerow(
                    [
                        "SKU123",
                        "Stainless Steel Insulated Tumbler",
                        "minimal_white",
                        "minimum",
                        "cm",
                        "Capacity: 500 ml",
                        "Double-wall insulation",
                        "Leak-proof lid",
                        "How to Use",
                        "Fill with your drink",
                        "Close the lid firmly",
                        "Enjoy hot or cold beverages",
                    ]
                )

            products = read_products_csv(csv_path)
            with self.assertRaises(ValidationError):
                generate_product_package(products[0], root / "out", batch_id="../BAD")

    def test_validator_rejects_path_like_expected_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product = ProductRow(
                product_id="SKU123",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )
            product_dir = generate_product_package(product, root / "out", batch_id=None)

            import json

            manifest_path = product_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_outputs"]["showcase"][0] = "../evil.png"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_outputs"]["showcase"][0] = "a\\b.png"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_outputs"]["showcase"][0] = "evil.txt"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

    def test_validator_rejects_directory_instead_of_expected_image(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product = ProductRow(
                product_id="SKU123",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )
            product_dir = generate_product_package(product, root / "out", batch_id=None)

            import json

            manifest = json.loads((product_dir / "manifest.json").read_text(encoding="utf-8"))
            expected = manifest["expected_outputs"]
            for category, files in expected.items():
                for fname in files[1:]:
                    (product_dir / category / fname).write_bytes(b"")

            bad_path = product_dir / "showcase" / expected["showcase"][0]
            bad_path.mkdir()

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

    def test_validator_rejects_missing_manifest_layout_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product = ProductRow(
                product_id="SKU123",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )
            product_dir = generate_product_package(product, root / "out", batch_id=None)
            (product_dir / "source").rmdir()

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=False)

    def test_validator_rejects_manifest_product_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product = ProductRow(
                product_id="SKU123",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )
            product_dir = generate_product_package(product, root / "out", batch_id=None)

            import json

            manifest_path = product_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["product"]["safe_product_id"] = "OTHER123"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=False)

    def test_validator_rejects_wrong_expected_output_count_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product = ProductRow(
                product_id="SKU123",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )
            product_dir = generate_product_package(product, root / "out", batch_id=None)

            import json

            manifest_path = product_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_outputs"]["showcase"] = [manifest["expected_outputs"]["showcase"][0]]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            duplicate_name = manifest["expected_outputs"]["spec"][0]
            manifest["expected_outputs"]["spec"] = [duplicate_name, duplicate_name]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValidationError):
                validate_product_package(product_dir, require_images=True)

    def test_manifest_json_must_be_object(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.json").write_text("[]\n", encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_product_package(root, require_images=False)

    def test_generate_rejects_unsafe_product_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_root = root / "out"

            p = ProductRow(
                product_id="SKU123!",
                product_name_en="Stainless Steel Insulated Tumbler",
                style_pack="minimal_white",
                output_set="minimum",
                units="cm",
                dimensions_l=None,
                dimensions_w=None,
                dimensions_h=None,
                specs=("Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"),
                howto_title="How to Use",
                steps=("Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"),
                tips=(),
                manager_notes=None,
                must_have_keywords=None,
                must_avoid_elements=None,
                personalization_text_en=None,
            )

            with self.assertRaises(ValidationError):
                generate_product_package(p, out_root, batch_id=None)

    def test_read_products_csv_rejects_unsafe_product_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "in.csv"

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "product_id",
                        "product_name_en",
                        "style_pack",
                        "output_set",
                        "units",
                        "spec_1",
                        "spec_2",
                        "spec_3",
                        "howto_title",
                        "step_1",
                        "step_2",
                        "step_3",
                    ]
                )
                w.writerow(
                    [
                        "SKU 123",
                        "Stainless Steel Insulated Tumbler",
                        "minimal_white",
                        "minimum",
                        "cm",
                        "Capacity: 500 ml",
                        "Double-wall insulation",
                        "Leak-proof lid",
                        "How to Use",
                        "Fill with your drink",
                        "Close the lid firmly",
                        "Enjoy hot or cold beverages",
                    ]
                )

            with self.assertRaises(ValidationError):
                read_products_csv(csv_path)

    def test_read_products_csv_rejects_non_ascii_english_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "in.csv"

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "product_id",
                        "product_name_en",
                        "style_pack",
                        "output_set",
                        "units",
                        "spec_1",
                        "spec_2",
                        "spec_3",
                        "howto_title",
                        "step_1",
                        "step_2",
                        "step_3",
                    ]
                )
                w.writerow(
                    [
                        "SKU123",
                        "Cafe\u00e9 Tumbler",
                        "minimal_white",
                        "minimum",
                        "cm",
                        "Capacity: 500 ml",
                        "Double-wall insulation",
                        "Leak-proof lid",
                        "How to Use",
                        "Fill with your drink",
                        "Close the lid firmly",
                        "Enjoy hot or cold beverages",
                    ]
                )

            with self.assertRaises(ValidationError):
                read_products_csv(csv_path)

    def test_cli_validate_missing_out_returns_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing_out"
            with redirect_stderr(StringIO()):
                code = cli_main(["validate", "--out", str(missing)])
            self.assertEqual(code, 2)

    def test_cli_generate_out_is_file_returns_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "in.csv"

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "product_id",
                        "product_name_en",
                        "style_pack",
                        "output_set",
                        "units",
                        "spec_1",
                        "spec_2",
                        "spec_3",
                        "howto_title",
                        "step_1",
                        "step_2",
                        "step_3",
                    ]
                )
                w.writerow(
                    [
                        "SKU123",
                        "Stainless Steel Insulated Tumbler",
                        "minimal_white",
                        "minimum",
                        "cm",
                        "Capacity: 500 ml",
                        "Double-wall insulation",
                        "Leak-proof lid",
                        "How to Use",
                        "Fill with your drink",
                        "Close the lid firmly",
                        "Enjoy hot or cold beverages",
                    ]
                )

            out_path = root / "out"
            out_path.write_text("not a dir", encoding="utf-8")

            with redirect_stderr(StringIO()):
                code = cli_main(["generate", "--input", str(csv_path), "--out", str(out_path)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
