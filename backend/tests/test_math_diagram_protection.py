from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from services.math.render_helper import render_prose_latex_to_html


class DiagramProtectionTests(unittest.TestCase):
    def test_generated_image_is_outside_display_math(self):
        image = '<div class="math-diagram-wrap"><img src="/api/math/diagrams/test.svg"></div>'
        for opening, closing in (('$$', '$$'), (r'\[', r'\]')):
            with self.subTest(opening=opening):
                rendered = render_prose_latex_to_html('Before.\n' + opening + '\n' + image + '\n' + closing + '\nAfter.')
                self.assertIn(image, rendered)
                self.assertNotIn(opening, rendered)
                self.assertIn('Before.', rendered)
                self.assertIn('After.', rendered)

    def test_display_with_additional_math_is_not_stripped(self):
        image = '<div class="math-diagram-wrap"><img src="test.svg"></div>'
        rendered = render_prose_latex_to_html('$$x + ' + image + '$$')
        self.assertIn('$$', rendered)

    def test_display_diagram_preserves_rows_and_labels(self):
        diagram = r"\[\xymatrix{A\ar[r]^f\ar[d]_u & B\ar[d]^v \\" + "\n" + r"C\ar[r]_g & D}\]"
        rendered = render_prose_latex_to_html("Before.\n\n" + diagram + "\n\nAfter.")
        self.assertIn(diagram, rendered)
        self.assertIn("Before.", rendered)
        self.assertIn("After.", rendered)

    def test_prose_breaks_still_convert(self):
        self.assertIn("<br>", render_prose_latex_to_html(r"First\\Second"))

    def test_equation_environment_still_preserves_rows(self):
        equation = r"\begin{align}a&=b\\c&=d\end{align}"
        self.assertIn(equation, render_prose_latex_to_html(equation))


if __name__ == "__main__":
    unittest.main()
