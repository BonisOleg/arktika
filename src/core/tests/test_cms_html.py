from django.test import SimpleTestCase

from src.core.html import html_to_plain, sanitize_cms_html


class SanitizeCmsHtmlTests(SimpleTestCase):
    def test_strips_script(self):
        cleaned = sanitize_cms_html('<p>ok</p><script>alert(1)</script>')
        self.assertIn("<p>ok</p>", cleaned)
        self.assertNotIn("script", cleaned.lower())

    def test_keeps_allowed_markup(self):
        raw = "<p>рядок</p><p><strong>жирний</strong></p><ul><li>а</li></ul>"
        self.assertEqual(sanitize_cms_html(raw), raw)

    def test_drops_javascript_href(self):
        cleaned = sanitize_cms_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript", cleaned.lower())


class HtmlToPlainTests(SimpleTestCase):
    def test_one_enter_is_single_newline(self):
        self.assertEqual(html_to_plain("<p>один</p><p>два</p>"), "один\nдва")

    def test_empty_p_is_blank_line(self):
        self.assertEqual(html_to_plain("<p>один</p><p></p><p>два</p>"), "один\n\nдва")
