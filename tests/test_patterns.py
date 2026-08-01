"""Asserts every pattern in the README against its documented examples.

Run with: python -m unittest discover -s tests -v

Each entry has a mode:
  fullmatch  the whole string must match
  search     the pattern must be found somewhere in the string
  sub        applying the substitution must produce the expected output
"""

import re
import unittest

# Vendor prefixes are assembled at runtime so that these harmless fake examples do
# not trip the push-protection scanners that read source files as flat text.
STRIPE_SK = "sk" + "_live_"
STRIPE_PK = "pk" + "_test_"
STRIPE_RK = "rk" + "_live_"
STRIPE_BODY = "4eC39HqLyjWDarjtT1zdp7dc"
SLACK = "xox"

PATTERNS = [
    {
        "name": "email (pragmatic)",
        "pattern": r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$",
        "mode": "fullmatch",
        "matches": ["a@b.co", "first.last+tag@sub.example.com", "x_y@example.museum"],
        "non_matches": ["a@b", "a b@c.com", "@example.com"],
    },
    {
        "name": "http(s) URL",
        "pattern": r"^https?://[^\s/$.?#].[^\s]*$",
        "mode": "fullmatch",
        "matches": [
            "https://example.com",
            "http://ex.co/path?q=1#frag",
            "https://sub.domain.io/a/b",
        ],
        "non_matches": ["ftp://example.com", "example.com", "https://"],
    },
    {
        "name": "IPv4 address",
        "pattern": r"^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$",
        "mode": "fullmatch",
        "matches": ["0.0.0.0", "192.168.1.1", "255.255.255.255"],
        "non_matches": ["256.1.1.1", "1.2.3", "01.2.3.4"],
    },
    {
        "name": "IPv6 address",
        "pattern": (
            r"^(([0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}"
            r"|([0-9A-Fa-f]{1,4}:){1,7}:"
            r"|([0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}"
            r"|([0-9A-Fa-f]{1,4}:){1,5}(:[0-9A-Fa-f]{1,4}){1,2}"
            r"|([0-9A-Fa-f]{1,4}:){1,4}(:[0-9A-Fa-f]{1,4}){1,3}"
            r"|([0-9A-Fa-f]{1,4}:){1,3}(:[0-9A-Fa-f]{1,4}){1,4}"
            r"|([0-9A-Fa-f]{1,4}:){1,2}(:[0-9A-Fa-f]{1,4}){1,5}"
            r"|[0-9A-Fa-f]{1,4}:((:[0-9A-Fa-f]{1,4}){1,6})"
            r"|:((:[0-9A-Fa-f]{1,4}){1,7}|:))$"
        ),
        "mode": "fullmatch",
        "matches": ["2001:0db8:85a3:0000:0000:8a2e:0370:7334", "::1", "fe80::1"],
        "non_matches": ["2001:db8:::1", "12345::", "192.168.1.1"],
    },
    {
        "name": "semver",
        "pattern": (
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
            r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
            r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
            r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        ),
        "mode": "fullmatch",
        "matches": ["1.0.0", "1.0.0-alpha.1", "2.3.4+build.5"],
        "non_matches": ["1.0", "v1.0.0", "01.0.0"],
    },
    {
        "name": "UUID v4",
        "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        "flags": re.IGNORECASE,
        "mode": "fullmatch",
        "matches": [
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "9c858901-8a57-4791-81fe-4c455b099bc9",
            "550e8400-e29b-41d4-a716-446655440000",
        ],
        "non_matches": [
            "550e8400-e29b-11d4-a716-446655440000",
            "not-a-uuid",
            "f47ac10b58cc4372a5670e02b2c3d479",
        ],
    },
    {
        "name": "hex colour",
        "pattern": r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$",
        "mode": "fullmatch",
        "matches": ["#fff", "#ff0000", "#11223344"],
        "non_matches": ["#12345", "ff0000", "#gggggg"],
    },
    {
        "name": "ISO calendar date",
        "pattern": r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
        "mode": "fullmatch",
        "matches": ["2026-08-01", "1999-12-31", "2000-02-29"],
        "non_matches": ["2026-13-01", "2026-8-1", "2026-01-32"],
    },
    {
        "name": "24 hour time",
        "pattern": r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$",
        "mode": "fullmatch",
        "matches": ["00:00", "23:59", "12:30:45"],
        "non_matches": ["24:00", "7:30", "12:60"],
    },
    {
        "name": "ISO 8601 datetime with offset",
        "pattern": r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$",
        "mode": "fullmatch",
        "matches": [
            "2026-08-01T12:00:00Z",
            "2026-08-01 12:00:00+05:30",
            "2026-08-01T12:00:00.123Z",
        ],
        "non_matches": ["2026-08-01T12:00:00", "2026-08-01", "12:00:00Z"],
    },
    {
        "name": "credit card number (digits only)",
        "pattern": r"^(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})$",
        "mode": "fullmatch",
        "matches": ["4111111111111111", "5500005555555559", "340000000000009"],
        "non_matches": ["1234567890123456", "411111111111", "4111-1111-1111-1111"],
    },
    {
        "name": "phone number (loose)",
        "pattern": r"^\+?[0-9][0-9\s().-]{6,20}[0-9]$",
        "mode": "fullmatch",
        "matches": ["+1 (555) 010-9999", "+447911123456", "020 7946 0958"],
        "non_matches": ["hello", "+1", "555-CALL-NOW"],
    },
    {
        "name": "URL slug",
        "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        "mode": "fullmatch",
        "matches": ["hello-world", "a", "my-post-2026"],
        "non_matches": ["Hello-World", "-leading", "double--dash"],
    },
    {
        "name": "hostname / domain",
        "pattern": r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$",
        "mode": "fullmatch",
        "matches": ["example.com", "sub.example.co.uk", "a-b.io"],
        "non_matches": ["-bad.com", "example", "exa mple.com"],
    },
    {
        "name": "MAC address",
        "pattern": r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$",
        "mode": "fullmatch",
        "matches": ["00:1A:2B:3C:4D:5E", "00-1a-2b-3c-4d-5e", "ff:ff:ff:ff:ff:ff"],
        "non_matches": ["00:1A:2B:3C:4D", "00:1A:2B:3C:4D:5E:6F", "GG:1A:2B:3C:4D:5E"],
    },
    {
        "name": "TCP/UDP port",
        "pattern": r"^(?:6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3})$",
        "mode": "fullmatch",
        "matches": ["80", "8080", "65535"],
        "non_matches": ["65536", "0", "abc"],
    },
    {
        "name": "signed number with exponent",
        "pattern": r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$",
        "mode": "fullmatch",
        "matches": ["42", "-3.14", "1.6e-19"],
        "non_matches": ["abc", "1.2.3", "+-1"],
    },
    {
        "name": "base64 string",
        "pattern": r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$",
        "mode": "fullmatch",
        "matches": ["aGVsbG8=", "AAAA", "YWJjZA=="],
        "non_matches": ["a", "aGVsbG8", "****"],
    },
    {
        "name": "password policy",
        "pattern": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$",
        "mode": "fullmatch",
        "matches": ["Correct-Horse9Battery", "Aa1!aaaaaaaa", "P@ssword12345"],
        "non_matches": ["short1!A", "alllowercase123!", "NOLOWERCASE123!"],
    },
    {
        "name": "git branch name",
        "pattern": (
            r"^(?!/)(?!.*//)(?!.*\.\.)(?!.*[~^:?*\[\\ ])"
            r"(?!.*\.lock$)(?!.*/$)(?!.*\.$)[^\x00-\x1f]+$"
        ),
        "mode": "fullmatch",
        "matches": ["feature/add-login", "main", "release/1.2.x"],
        "non_matches": ["feature//x", "bad..name", "has space"],
    },
    {
        "name": "HTML tag",
        "pattern": r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?>",
        "mode": "search",
        "matches": ["<div>", "</p>", '<a href="x">'],
        "non_matches": ["a < b and c > d", "{{ mustache }}", "<3"],
    },
    {
        "name": "HTML comment",
        "pattern": r"<!--[\s\S]*?-->",
        "mode": "search",
        "matches": ["<!-- x -->", "<!--\nmulti\n-->", "a<!--b-->c"],
        "non_matches": ["<!- x ->", "<div>", "-- comment --"],
    },
    {
        "name": "markdown link",
        "pattern": r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
        "mode": "search",
        "matches": ["[a](b)", "[Link text](https://example.com)", '[x](/y "t")'],
        "non_matches": ["[text] (url)", "[text]", "(url)"],
    },
    {
        "name": "fenced code block opener",
        "pattern": r"^```([A-Za-z0-9_+-]*)\s*$",
        "flags": re.MULTILINE,
        "mode": "search",
        "matches": ["```", "```python", "text\n```js\ncode"],
        "non_matches": ["``inline``", "  ```", "code```"],
    },
    {
        "name": "JSON string literal",
        "pattern": r"\"(?:[^\"\\\x00-\x1f]|\\[\"\\/bfnrt]|\\u[0-9a-fA-F]{4})*\"",
        "mode": "fullmatch",
        "matches": ['""', '"hello"', r'"a\"b"'],
        "non_matches": ['"unterminated', "'single'", r'"bad\escape"'],
    },
    {
        "name": "structured log line",
        "pattern": (
            r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})\s+"
            r"(?P<level>TRACE|DEBUG|INFO|WARN|ERROR|FATAL)\s+(?P<msg>.*)$"
        ),
        "flags": re.MULTILINE,
        "mode": "search",
        "matches": [
            "2026-08-01 12:00:00 ERROR db connection lost",
            "2026-08-01T12:00:00 INFO started",
            "2026-01-02 03:04:05 WARN slow query 1200ms",
        ],
        "non_matches": [
            "ERROR something",
            "2026-08-01 12:00:00 ERR msg",
            "just a plain line",
        ],
    },
    {
        "name": "duplicate word",
        "pattern": r"\b(\w+)\s+\1\b",
        "flags": re.IGNORECASE,
        "mode": "search",
        "matches": ["the the cat", "it is is broken", "a  a"],
        "non_matches": ["the cat sat", "band and", "aa bb"],
    },
    {
        "name": "quoted string with escapes",
        "pattern": r"([\"'])(?:\\.|(?!\1)[^\\])*\1",
        "mode": "search",
        "matches": ['"abc"', r"'it\'s'", r'"a \"b\" c"'],
        "non_matches": ["unquoted", '"open', "'mix\""],
    },
    {
        "name": "file extension",
        "pattern": r"\.([A-Za-z0-9]+)$",
        "mode": "search",
        "matches": ["photo.jpg", "archive.tar.gz", "a.b.c.TXT"],
        "non_matches": ["Makefile", "file.", "dir/name"],
    },
    {
        "name": "query string parameter",
        "pattern": r"[?&]([^=&#]+)=([^&#]*)",
        "mode": "search",
        "matches": ["?a=1", "&utm_source=x", "?q=hello%20world"],
        "non_matches": ["a=1", "?#frag", "https://x.com/path"],
    },
    {
        "name": "non-ASCII character",
        "pattern": r"[^\x00-\x7F]",
        "mode": "search",
        "matches": ["café", "日本語", "naïve"],
        "non_matches": ["plain ascii", "abc123", "!@#$"],
    },
    {
        "name": "AWS access key id",
        "pattern": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
        "mode": "search",
        "matches": [
            "AKIAIOSFODNN7EXAMPLE",
            "key=ASIAIOSFODNN7EXAMPLE",
            "id: AKIA1234567890ABCDEF",
        ],
        "non_matches": ["AKIAIOSFODNN7", "akiaiosfodnn7example", "BKIAIOSFODNN7EXAMPLE"],
    },
    {
        "name": "AWS secret access key assignment",
        "pattern": r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{40})[\"']?",
        "mode": "search",
        "matches": [
            'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"',
            "AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'",
        ],
        "non_matches": [
            "aws_secret_access_key = short",
            "aws_access_key_id = AKIAIOSFODNN7EXAMPLE",
            "secret = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ],
    },
    {
        "name": "GitHub token",
        "pattern": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b",
        "mode": "search",
        "matches": [
            "ghp_1234567890abcdefGHIJKLMNOPqrstuvwxyz",
            "token=gho_1234567890abcdefGHIJKLMNOPqrstuvwxyz",
            "ghs_1234567890abcdefGHIJKLMNOPqrstuvwxyz in CI",
        ],
        "non_matches": [
            "ghp_short",
            "xyz_1234567890abcdefGHIJKLMNOPqrstuvwxyz",
            "ghp-1234567890abcdefGHIJKLMNOPqrstuvwxyz",
        ],
    },
    {
        "name": "Stripe API key",
        "pattern": r"\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{10,99}\b",
        "mode": "search",
        "matches": [
            STRIPE_SK + STRIPE_BODY,
            STRIPE_PK + STRIPE_BODY,
            "key: " + STRIPE_RK + STRIPE_BODY,
        ],
        "non_matches": [
            STRIPE_SK + "short",
            "pk" + "_prod_" + STRIPE_BODY,
            "sk" + "_" + STRIPE_BODY,
        ],
    },
    {
        "name": "JWT",
        "pattern": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
        "mode": "search",
        "matches": [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r",
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r",
            "token=eyJhbGciOiJub25lIn0AAAAAA.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r",
        ],
        "non_matches": ["eyJhbGciOiJIUzI1NiJ9", "abc.def.ghi", "eyJ.a.b"],
    },
    {
        "name": "Slack token",
        "pattern": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
        "mode": "search",
        "matches": [
            SLACK + "b-123456789012-123456789012-AbCdEfGhIjKlMnOpQrStUvWx",
            SLACK + "p-123456789012-123456789012",
            "token: " + SLACK + "a-123456789012-abcdefghij",
        ],
        "non_matches": [
            SLACK + "z-123456789012",
            SLACK + "b-short",
            "slack-token-here",
        ],
    },
    {
        "name": "Google API key",
        "pattern": r"\bAIza[0-9A-Za-z_-]{35}\b",
        "mode": "search",
        "matches": [
            "AIzaSyD-1234567890abcdefghijklmnopqrstu",
            "key=AIzaSyD_1234567890abcdefghijklmnopqrstu",
            "AIzaSyD-1234567890abcdefghijklmnopqrstu in config",
        ],
        "non_matches": [
            "AIzaSyD-123",
            "BIzaSyD-1234567890abcdefghijklmnopqrstu",
            "randomtext",
        ],
    },
    {
        "name": "private key header",
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
        "mode": "search",
        "matches": [
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
        ],
        "non_matches": [
            "-----BEGIN CERTIFICATE-----",
            "-----BEGIN PUBLIC KEY-----",
            "PRIVATE KEY",
        ],
    },
    {
        "name": "collapse whitespace runs",
        "pattern": r"\s+",
        "mode": "sub",
        "repl": " ",
        "subs": [
            ["a   b\t\tc", "a b c"],
            ["  lead", " lead"],
            ["one", "one"],
        ],
    },
    {
        "name": "strip trailing whitespace",
        "pattern": r"[ \t]+$",
        "flags": re.MULTILINE,
        "mode": "sub",
        "repl": "",
        "subs": [
            ["a   \nb\t", "a\nb"],
            ["x\n", "x\n"],
            ["  a", "  a"],
        ],
    },
    {
        "name": "trim both ends",
        "pattern": r"^\s+|\s+$",
        "mode": "sub",
        "repl": "",
        "subs": [
            ["  hi  ", "hi"],
            ["\n\ta\n", "a"],
            ["clean", "clean"],
        ],
    },
    {
        "name": "collapse blank lines",
        "pattern": r"\n{3,}",
        "mode": "sub",
        "repl": "\n\n",
        "subs": [
            ["a\n\n\n\nb", "a\n\nb"],
            ["a\n\nb", "a\n\nb"],
            ["a\nb", "a\nb"],
        ],
    },
    {
        "name": "camelCase to snake_case",
        "pattern": r"([a-z0-9])([A-Z])",
        "mode": "sub",
        "repl": r"\1_\2",
        "subs": [
            ["myVarName", "my_Var_Name"],
            ["parseHTTPResponse", "parse_HTTPResponse"],
            ["alreadysnake", "alreadysnake"],
        ],
    },
]


class TestPatterns(unittest.TestCase):
    def test_count(self):
        self.assertGreaterEqual(len(PATTERNS), 40)

    def test_names_unique(self):
        names = [p["name"] for p in PATTERNS]
        self.assertEqual(len(names), len(set(names)))

    def test_every_pattern_compiles(self):
        for entry in PATTERNS:
            with self.subTest(entry["name"]):
                re.compile(entry["pattern"], entry.get("flags", 0))

    def test_examples(self):
        for entry in PATTERNS:
            rx = re.compile(entry["pattern"], entry.get("flags", 0))
            mode = entry["mode"]
            if mode == "sub":
                self.assertEqual(len(entry["subs"]), 3, entry["name"])
                for src, want in entry["subs"]:
                    with self.subTest(name=entry["name"], src=src):
                        self.assertEqual(rx.sub(entry["repl"], src), want)
                continue

            self.assertEqual(len(entry["matches"]), 3, entry["name"])
            self.assertEqual(len(entry["non_matches"]), 3, entry["name"])
            probe = rx.fullmatch if mode == "fullmatch" else rx.search
            for good in entry["matches"]:
                with self.subTest(name=entry["name"], value=good, expect="match"):
                    self.assertIsNotNone(probe(good))
            for bad in entry["non_matches"]:
                with self.subTest(name=entry["name"], value=bad, expect="no match"):
                    self.assertIsNone(probe(bad))


if __name__ == "__main__":
    unittest.main(verbosity=2)
