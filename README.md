# regex-cookbook

Copy-paste regex for the 44 things you actually need, each one proved by a real test suite.

<p align="center">
  <img src="assets/demo.gif" alt="regex-cookbook demo" width="780">
</p>

## Start here

- [The patterns](#the-patterns), all 44 with matches, non-matches and the trap in each one.
- [ReDoS: the warning you should actually read](#redos-the-warning-you-should-actually-read), before you ship a pattern that hangs on user input.
- [Syntax cheat table](#syntax-cheat-table), for the token you half remember.

Every other regex list gives you a pattern and no way to know whether it is right. This one ships `tests/test_patterns.py`, which asserts all 44 patterns against three matching and three non-matching strings each, so a broken entry fails CI instead of quietly breaking your validation. It also tells you where each pattern is a bad idea, because half of the regexes people copy (email, phone, credit card) should not be regexes at all.

## Install

There is nothing to install. Clone it, copy the pattern you need, and run the tests if you change one.

```bash
git clone https://github.com/botaoishere/regex-cookbook
cd regex-cookbook
python -m unittest discover -s tests -v
```

## Usage

```
$ python -m unittest discover -s tests
....
----------------------------------------------------------------------
Ran 4 tests in 0.004s

OK
```

Patterns are written for Python `re` and tested there. Flavour notes on each entry tell you what changes in JavaScript, PCRE (PHP, Perl, most CLI tools) and RE2 (Go, and Google-adjacent things). The two rules that cover most of it: RE2 has no backreferences and no lookaround at all, and JavaScript needs the `u` flag before `\p{...}` works.

## Syntax cheat table

| Token | Means | Gotcha |
| --- | --- | --- |
| `.` | any char except newline | add `s` / `DOTALL` to include newlines |
| `\d \w \s` | digit, word char, whitespace | in Python these are Unicode-aware by default, in JS they are ASCII-only |
| `^ $` | start / end of string | with `MULTILINE` they mean start / end of line, and `$` also matches before a final newline |
| `\A \z` | true start / true end | use these when `$` matching before a trailing newline would be a bug |
| `*  +  ?` | 0+, 1+, 0 or 1 | greedy by default |
| `*? +? ??` | same, lazy | lazy is not free, it just backtracks in the other direction |
| `{n,m}` | between n and m | `{,m}` is a literal in some engines, always write `{0,m}` |
| `[abc]` `[^abc]` | class, negated class | inside a class only `^ ] - \` are special |
| `(?:...)` | group without capturing | use this by default, capture only what you read |
| `(?<name>...)` | named capture | Python also accepts `(?P<name>...)`, older JS engines accept neither |
| `(?=...)` `(?!...)` | lookahead, positive / negative | zero width, consumes nothing, unsupported in RE2 |
| `\b` | word boundary | it is a boundary between `\w` and non-`\w`, so `\bfoo\b` will not match inside `foo_bar` |

## ReDoS: the warning you should actually read

Catastrophic backtracking is a denial of service you ship yourself. It happens when nested quantifiers can split the same input in exponentially many ways, and the classic shape is `(a+)+$`.

```python
import re, time
rx = re.compile(r"^(a+)+$")
s = "a" * 30 + "!"          # 30 a's, then one character that cannot match
t = time.time(); rx.search(s); print(time.time() - t)   # seconds, not microseconds
```

Add one more `a` and the time doubles. The same shape hides in innocent-looking patterns: `^(\s*\w+)+$`, `^(\w+\s?)*$`, `(.*,)*`. Rules that keep you out of trouble:

1. Never nest an unbounded quantifier inside another unbounded quantifier.
2. Make alternation branches mutually exclusive, so the engine has nothing to retry.
3. Anchor and bound: `{1,64}` instead of `+` on anything user-supplied.
4. If the input comes from a user and the pattern is non-trivial, use RE2 (Go's `regexp`, Python's `re2` bindings, Rust's `regex`). RE2 gives up expressive power in exchange for a linear-time guarantee, which is the right trade for untrusted input.
5. Time-box it. Python has no regex timeout, so on a hot path validate length first and reject anything absurd before the regex sees it.

---

## The patterns

### 1. Email (pragmatic)

```
^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$
```

Flavour: portable across JS, Python, PCRE and RE2.
Matches: `a@b.co`, `first.last+tag@sub.example.com`, `x_y@example.museum`
No match: `a@b`, `a b@c.com`, `@example.com`
Trap: do not do this. RFC 5322 allows quoted local parts, comments and addresses this rejects, and every stricter regex you find rejects more valid addresses than it catches invalid ones. Use this only to catch typos in a form, then send a confirmation email. Deliverability is the only real validation.

### 2. HTTP(S) URL

```
^https?://[^\s/$.?#].[^\s]*$
```

Flavour: portable.
Matches: `https://example.com`, `http://ex.co/path?q=1#frag`, `https://sub.domain.io/a/b`
No match: `ftp://example.com`, `example.com`, `https://`
Trap: this checks shape, not validity. It happily accepts `https://not a real host`-free garbage like `https://...`. If your language has a URL parser (`new URL()`, `urllib.parse`), parse first and use the regex only to pre-filter text.

### 3. IPv4 address

```
^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$
```

Flavour: portable.
Matches: `0.0.0.0`, `192.168.1.1`, `255.255.255.255`
No match: `256.1.1.1`, `1.2.3`, `01.2.3.4`
Trap: leading zeros are rejected on purpose, because `inet_aton` treats `010` as octal 8 and that mismatch has been a real SSRF bypass. Order of alternatives matters: put the longer branches first or `25[0-5]` never gets a chance.

### 4. IPv6 address

```
^(([0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}|([0-9A-Fa-f]{1,4}:){1,7}:|([0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}|([0-9A-Fa-f]{1,4}:){1,5}(:[0-9A-Fa-f]{1,4}){1,2}|([0-9A-Fa-f]{1,4}:){1,4}(:[0-9A-Fa-f]{1,4}){1,3}|([0-9A-Fa-f]{1,4}:){1,3}(:[0-9A-Fa-f]{1,4}){1,4}|([0-9A-Fa-f]{1,4}:){1,2}(:[0-9A-Fa-f]{1,4}){1,5}|[0-9A-Fa-f]{1,4}:((:[0-9A-Fa-f]{1,4}){1,6})|:((:[0-9A-Fa-f]{1,4}){1,7}|:))$
```

Flavour: portable, but ugly everywhere.
Matches: `2001:0db8:85a3:0000:0000:8a2e:0370:7334`, `::1`, `fe80::1`
No match: `2001:db8:::1`, `12345::`, `192.168.1.1`
Trap: it does not handle zone ids (`fe80::1%eth0`) or IPv4-mapped forms (`::ffff:192.0.2.1`). If you need those, use `inet_pton` and stop. This pattern exists for grepping logs, not for validation.

### 5. Semantic version

```
^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$
```

Flavour: portable. This is the regex published on semver.org.
Matches: `1.0.0`, `1.0.0-alpha.1`, `2.3.4+build.5`
No match: `1.0`, `v1.0.0`, `01.0.0`
Trap: it deliberately rejects the leading `v` that half of the ecosystem uses in tags. Strip the `v` before matching rather than loosening the pattern.

### 6. UUID v4

```
^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
```

Flavour: needs the case-insensitive flag (`i`, `re.IGNORECASE`).
Matches: `f47ac10b-58cc-4372-a567-0e02b2c3d479`, `9c858901-8a57-4791-81fe-4c455b099bc9`, `550e8400-e29b-41d4-a716-446655440000`
No match: `550e8400-e29b-11d4-a716-446655440000`, `not-a-uuid`, `f47ac10b58cc4372a5670e02b2c3d479`
Trap: the `4` and the `[89ab]` pin the version and variant nibbles. If you are also handling v1 or v7 UUIDs, replace both with `[0-9a-f]` or you will reject valid ids from your own database.

### 7. Hex colour

```
^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$
```

Flavour: portable.
Matches: `#fff`, `#ff0000`, `#11223344`
No match: `#12345`, `ff0000`, `#gggggg`
Trap: the alternation order matters. `[0-9a-fA-F]{3,8}` would accept the invalid 5 and 7 digit forms, so the lengths are enumerated instead.

### 8. ISO calendar date

```
^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$
```

Flavour: portable.
Matches: `2026-08-01`, `1999-12-31`, `2000-02-29`
No match: `2026-13-01`, `2026-8-1`, `2026-01-32`
Trap: this accepts `2026-02-31`. Regex cannot count days in a month or know about leap years. Match the shape, then parse it with a date library and let the parse failure be your real validation.

### 9. Time, 24 hour

```
^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$
```

Flavour: portable.
Matches: `00:00`, `23:59`, `12:30:45`
No match: `24:00`, `7:30`, `12:60`
Trap: leap seconds are real and `23:59:60` is a legal time that this rejects. Widen the seconds group to `[0-6]\d` only if you actually ingest data that has them.

### 10. ISO 8601 datetime with offset

```
^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$
```

Flavour: portable.
Matches: `2026-08-01T12:00:00Z`, `2026-08-01 12:00:00+05:30`, `2026-08-01T12:00:00.123Z`
No match: `2026-08-01T12:00:00`, `2026-08-01`, `12:00:00Z`
Trap: requiring the offset is the point. A timestamp without a zone is ambiguous, and the bug it causes appears twice a year at 2am. Some producers emit `+0530` with no colon, so make the colon optional if you must accept them.

### 11. Credit card number (digits only)

```
^(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})$
```

Flavour: portable. Strip spaces and dashes before matching.
Matches: `4111111111111111`, `5500005555555559`, `340000000000009`
No match: `1234567890123456`, `411111111111`, `4111-1111-1111-1111`
Trap: this identifies a brand, it does not validate a card. You still need the Luhn checksum, and even then only the payment processor knows if the card is real. Also never log the input you tested. Best answer: use a hosted card field and never let the number reach your server.

### 12. Phone number (loose)

```
^\+?[0-9][0-9\s().-]{6,20}[0-9]$
```

Flavour: portable.
Matches: `+1 (555) 010-9999`, `+447911123456`, `020 7946 0958`
No match: `hello`, `+1`, `555-CALL-NOW`
Trap: you cannot validate phone numbers with a regex. Numbering plans differ per country, change over time, and vanity numbers are legal. Use libphonenumber, or accept anything vaguely numeric and verify by sending a code.

### 13. URL slug

```
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Flavour: portable.
Matches: `hello-world`, `a`, `my-post-2026`
No match: `Hello-World`, `-leading`, `double--dash`
Trap: writing it as `^[a-z0-9-]+$` is the common mistake, because that allows leading, trailing and doubled hyphens. The group-and-repeat form structurally forbids them.

### 14. Hostname or domain

```
^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$
```

Flavour: portable.
Matches: `example.com`, `sub.example.co.uk`, `a-b.io`
No match: `-bad.com`, `example`, `exa mple.com`
Trap: it rejects internationalised domains, which arrive as punycode (`xn--...`) if you normalise first and as Unicode if you do not. Normalise to punycode before matching. It also rejects the trailing dot of a fully qualified name, which is legal in DNS.

### 15. MAC address

```
^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$
```

Flavour: portable.
Matches: `00:1A:2B:3C:4D:5E`, `00-1a-2b-3c-4d-5e`, `ff:ff:ff:ff:ff:ff`
No match: `00:1A:2B:3C:4D`, `00:1A:2B:3C:4D:5E:6F`, `GG:1A:2B:3C:4D:5E`
Trap: it accepts mixed separators like `00:1A-2B:3C-4D:5E`. Fixing that needs a backreference (`([:-])` then `\1`), which RE2 will not compile.

### 16. TCP/UDP port

```
^(?:6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3})$
```

Flavour: portable.
Matches: `80`, `8080`, `65535`
No match: `65536`, `0`, `abc`
Trap: numeric range regexes are always this ugly, and they are almost always the wrong tool. `0 < int(s) <= 65535` is clearer and faster. Use this only when you are extracting ports out of unstructured text.

### 17. Signed number with exponent

```
^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$
```

Flavour: portable.
Matches: `42`, `-3.14`, `1.6e-19`
No match: `abc`, `1.2.3`, `+-1`
Trap: it rejects `Infinity`, `NaN` and hex floats, and it accepts `42.` which some parsers do not. If the destination is a real parser, try the parse and catch the error instead.

### 18. Base64 string

```
^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$
```

Flavour: portable.
Matches: `aGVsbG8=`, `AAAA`, `YWJjZA==`
No match: `a`, `aGVsbG8`, `****`
Trap: it matches the empty string, and it rejects URL-safe base64, which uses `-` and `_` instead of `+` and `/` and often drops the padding. Also, "looks like base64" is not "is base64": `AAAA` is a perfectly good English-free string that happens to decode.

### 19. Password policy

```
^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$
```

Flavour: lookahead, so JS, Python and PCRE only. RE2 cannot compile it.
Matches: `Correct-Horse9Battery`, `Aa1!aaaaaaaa`, `P@ssword12345`
No match: `short1!A`, `alllowercase123!`, `NOLOWERCASE123!`
Trap: you should not ship this. Composition rules push users toward `Password1!`, which this accepts and which is in every cracking dictionary. Current guidance (NIST SP 800-63B) is a length minimum, a check against a breached-password list, and nothing else. Note also that `.` does not match newlines, so a passphrase pasted with a newline fails confusingly.

### 20. Git branch name

```
^(?!/)(?!.*//)(?!.*\.\.)(?!.*[~^:?*\[\\ ])(?!.*\.lock$)(?!.*/$)(?!.*\.$)[^\x00-\x1f]+$
```

Flavour: lookahead, so no RE2.
Matches: `feature/add-login`, `main`, `release/1.2.x`
No match: `feature//x`, `bad..name`, `has space`
Trap: this is a good approximation of `git check-ref-format`, not a replacement for it. If git is already installed where this runs, shell out to `git check-ref-format --branch "$name"` and trust the exit code.

### 21. HTML tag

```
</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?>
```

Flavour: portable. Use it as a search, not a full match.
Matches: `<div>`, `</p>`, `<a href="x">`
No match: `a < b and c > d`, `{{ mustache }}`, `<3`
Trap: do not parse HTML with regex. This breaks on attributes containing `>` (`<a title="a>b">`), on `<script>` bodies, and on comments. It is fine for stripping tags out of trusted output for a word count, and unsafe for anything security-relevant. Use an HTML parser.

### 22. HTML comment

```
<!--[\s\S]*?-->
```

Flavour: `[\s\S]` is the portable way to say "any character including newlines" without needing the dotall flag.
Matches: `<!-- x -->`, a comment spanning several lines, `a<!--b-->c`
No match: `<!- x ->`, `<div>`, `-- comment --`
Trap: the lazy `*?` is what stops one match swallowing everything between the first `<!--` and the last `-->`. Removing comments this way can still change meaning, since conditional comments and `<!-- -->` inside a script string are not comments at all.

### 23. Markdown link

```
\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)
```

Flavour: portable. Group 1 is the text, group 2 the target, group 3 the optional title.
Matches: `[a](b)`, `[Link text](https://example.com)`, `[x](/y "t")`
No match: `[text] (url)`, `[text]`, `(url)`
Trap: it cannot handle a URL containing balanced parentheses, which Wikipedia links are full of, and it will match inside a fenced code block. Strip code fences first or use a Markdown AST.

### 24. Fenced code block opener

```
^```([A-Za-z0-9_+-]*)\s*$
```

Flavour: needs the multiline flag. Group 1 is the language hint.
Matches: ` ``` `, ` ```python `, a ` ```js ` line inside a larger document
No match: `` ``inline`` ``, an indented ` ``` `, `code``` `
Trap: CommonMark allows a fence to be indented by up to three spaces and allows tilde fences (`~~~`), both of which this misses. It also cannot tell an opening fence from a closing one, because they are the same token. Track state if that matters.

### 25. JSON string literal

```
"(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"
```

Flavour: portable.
Matches: `""`, `"hello"`, `"a\"b"`
No match: `"unterminated`, `'single'`, `"bad\escape"`
Trap: the naive `"[^"]*"` is wrong the moment a string contains an escaped quote. This version is correct per the JSON grammar, but it still does not validate surrogate pairs in `\uXXXX` escapes.

### 26. Structured log line

```
^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})\s+(?P<level>TRACE|DEBUG|INFO|WARN|ERROR|FATAL)\s+(?P<msg>.*)$
```

Flavour: Python named groups. JS and PCRE use `(?<ts>...)`; RE2 supports named groups too.
Matches: `2026-08-01 12:00:00 ERROR db connection lost`, `2026-08-01T12:00:00 INFO started`, `2026-01-02 03:04:05 WARN slow query 1200ms`
No match: `ERROR something`, `2026-08-01 12:00:00 ERR msg`, `just a plain line`
Trap: `.*` will not cross a newline, so multi-line stack traces come through as unmatched orphan lines. Buffer any line that fails to match onto the previous message.

### 27. Duplicate word

```
\b(\w+)\s+\1\b
```

Flavour: backreference, so no RE2. Add the case-insensitive flag.
Matches: `the the cat`, `it is is broken`, `a  a`
No match: `the cat sat`, `band and`, `aa bb`
Trap: `\s+` crosses newlines, which is exactly what you want for prose in a text editor and exactly what you do not want when the second word is the first word of the next list item. Use `[ \t]+` for the line-local version.

### 28. Quoted string with escapes

```
(["'])(?:\\.|(?!\1)[^\\])*\1
```

Flavour: backreference and lookahead, so no RE2.
Matches: `"abc"`, `'it\'s'`, `"a \"b\" c"`
No match: `unquoted`, `"open`, `'mix"`
Trap: `\1` forces the closing quote to match the opening one, and `(?!\1)` lets the other quote character appear freely inside. Without both, `'a" b'` breaks. This still does not understand comments, so a quote inside a code comment will start a phantom string.

### 29. File extension

```
\.([A-Za-z0-9]+)$
```

Flavour: portable. Search, not full match.
Matches: `photo.jpg`, `archive.tar.gz`, `a.b.c.TXT`
No match: `Makefile`, `file.`, `dir/name`
Trap: it returns `gz` for `archive.tar.gz`, which is the honest answer to "the extension" and the wrong answer to "the format". It also treats `.gitignore` as extension `gitignore`. Use your language's path library if you care about either case.

### 30. Query string parameter

```
[?&]([^=&#]+)=([^&#]*)
```

Flavour: portable.
Matches: `?a=1`, `&utm_source=x`, `?q=hello%20world`
No match: `a=1`, `?#frag`, `https://x.com/path`
Trap: it returns values still percent-encoded, and it does not handle repeated keys or PHP-style `a[]=1` array syntax. Use a query-string parser for real work; this is for pulling parameters out of log lines.

### 31. Non-ASCII character

```
[^\x00-\x7F]
```

Flavour: portable. In JS, add the `u` flag if you plan to reason about code points rather than UTF-16 units.
Matches: `café`, `日本語`, `naïve`
No match: `plain ascii`, `abc123`, `!@#$`
Trap: this is a "does this file have Unicode in it" smoke test, not a validity check. It flags smart quotes pasted from a document, which is usually what you were actually looking for.

### 32. AWS access key id

```
\b(?:AKIA|ASIA)[0-9A-Z]{16}\b
```

Flavour: portable.
Matches: `AKIAIOSFODNN7EXAMPLE`, `key=ASIAIOSFODNN7EXAMPLE`, `id: AKIA1234567890ABCDEF`
No match: `AKIAIOSFODNN7`, `akiaiosfodnn7example`, `BKIAIOSFODNN7EXAMPLE`
Trap: `ASIA` is a temporary session key and is far less alarming than `AKIA`, so alert on them differently. Access key ids are not secret on their own; the pattern below is the one that matters.

### 33. AWS secret access key assignment

```
(?i)aws_secret_access_key\s*[:=]\s*["']?([A-Za-z0-9/+=]{40})["']?
```

Flavour: inline `(?i)` works in Python, PCRE and Go; in JS use the `i` flag instead.
Matches: `aws_secret_access_key = "wJalr..."`, `AWS_SECRET_ACCESS_KEY: wJalr...`, `aws_secret_access_key='wJalr...'`
No match: `aws_secret_access_key = short`, `aws_access_key_id = AKIAIOSFODNN7EXAMPLE`, `secret = wJalr...`
Trap: a bare 40-character base64-ish string is unsearchable on its own, so this anchors on the variable name. That means a secret assigned to `SECRET` or passed positionally slips straight through. Secret scanning by regex is a net with known holes; pair it with a provider that can verify a candidate key.

### 34. GitHub token

```
\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b
```

Flavour: portable.
Matches: `ghp_...` (personal), `gho_...` (OAuth), `ghs_...` (server-to-server)
No match: `ghp_short`, `xyz_...`, `ghp-...`
Trap: GitHub's newer fine-grained tokens use the `github_pat_` prefix and a different length, so add `\bgithub_pat_[A-Za-z0-9_]{22,}\b` if you want full coverage. The good news is GitHub revokes tokens it sees pushed publicly, so a hit in a private repo is the urgent one.

### 35. Stripe API key

```
\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{10,99}\b
```

Flavour: portable.
Matches: `sk_live_` followed by 24 alphanumerics, the same with `pk_test_`, the same with `rk_live_`
No match: `sk_live_short`, `pk_prod_` plus 24 alphanumerics, a bare `sk_` with no environment segment
Trap: `pk_` keys are publishable and belong in front-end code, so alerting on them is noise. Alert on `sk_live` and `rk_live` only, and treat `sk_test` as a lint warning.

### 36. JWT

```
\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b
```

Flavour: portable.
Matches: a bare token, one behind `Authorization: Bearer`, one in `token=...`
No match: `eyJhbGciOiJIUzI1NiJ9`, `abc.def.ghi`, `eyJ.a.b`
Trap: `eyJ` is just base64url for `{"`, so this matches any three-part base64url string that starts with a JSON object, signed or not. Decode the header and check for an `alg` before you treat a hit as real. Unsigned tokens (`"alg":"none"`) match too, and those are their own kind of finding.

### 37. Slack token

```
\bxox[baprs]-[A-Za-z0-9-]{10,}\b
```

Flavour: portable.
Matches: `xoxb-...` (bot), `xoxp-...` (user), `xoxa-...` (app)
No match: `xoxz-...`, `xoxb-short`, `slack-token-here`
Trap: Slack has added prefixes over the years, so an unknown letter after `xox` is worth flagging manually rather than silently ignoring. Incoming webhook URLs (`hooks.slack.com/services/...`) are equally dangerous and this does not cover them.

### 38. Google API key

```
\bAIza[0-9A-Za-z_-]{35}\b
```

Flavour: portable.
Matches: `AIzaSyD-...`, `key=AIzaSyD_...`, a key sitting in a config line
No match: `AIzaSyD-123`, `BIzaSyD-...`, `randomtext`
Trap: Google API keys are often legitimately shipped in client-side code and restricted by referrer or IP instead. Before panicking, check whether the key has restrictions; an unrestricted key in a public bundle is the actual finding.

### 39. Private key header

```
-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----
```

Flavour: portable.
Matches: `-----BEGIN RSA PRIVATE KEY-----`, `-----BEGIN PRIVATE KEY-----`, `-----BEGIN OPENSSH PRIVATE KEY-----`
No match: `-----BEGIN CERTIFICATE-----`, `-----BEGIN PUBLIC KEY-----`, `PRIVATE KEY`
Trap: this is the highest-signal secret pattern in the list and it is essentially free of false positives, so run it on every commit. It will also fire on test fixtures, which is fine: a key committed as a fixture is still a key someone will copy.

### 40. Collapse whitespace runs

```
\s+   ->   " "
```

Flavour: portable substitution.
`"a   b\t\tc"` becomes `"a b c"`, `"  lead"` becomes `" lead"`, `"one"` stays `"one"`
Trap: `\s` includes newlines, so this flattens paragraphs into one line. Use `[ \t]+` when you want to keep the line structure, and remember Python's `\s` also matches Unicode spaces such as the non-breaking space, while JavaScript's does not without care.

### 41. Strip trailing whitespace

```
[ \t]+$   ->   ""
```

Flavour: needs the multiline flag to hit every line.
`"a   \nb\t"` becomes `"a\nb"`, `"x\n"` is unchanged, `"  a"` is unchanged
Trap: using `\s+$` instead would eat the newlines themselves and join your lines together, because `\s` matches `\n`. This is the single most common version of that mistake.

### 42. Trim both ends

```
^\s+|\s+$   ->   ""
```

Flavour: portable, but every language already has `.trim()` or `.strip()`, which is faster and clearer.
`"  hi  "` becomes `"hi"`, `"\n\ta\n"` becomes `"a"`, `"clean"` is unchanged
Trap: without the multiline flag this trims the whole string, which is what you want. With the multiline flag it trims every line, which is a different operation people reach for by accident.

### 43. Collapse blank lines

```
\n{3,}   ->   "\n\n"
```

Flavour: portable.
`"a\n\n\n\nb"` becomes `"a\n\nb"`, `"a\n\nb"` is unchanged, `"a\nb"` is unchanged
Trap: normalise `\r\n` to `\n` first or Windows files will not collapse at all. `{3,}` and not `{2,}`, because two newlines is one blank line and that is the thing you are keeping.

### 44. camelCase to snake_case

```
([a-z0-9])([A-Z])   ->   \1_\2      then lowercase the result
```

Flavour: portable substitution. JavaScript writes the replacement as `$1_$2`.
`"myVarName"` becomes `"my_Var_Name"`, `"parseHTTPResponse"` becomes `"parse_HTTPResponse"`, `"alreadysnake"` is unchanged
Trap: acronyms. `parseHTTPResponse` should become `parse_http_response` and this gives `parse_httpresponse` after lowercasing. The fix is two passes: first `(.)([A-Z][a-z]+)` then `([a-z0-9])([A-Z])`. Test with `HTTPServer`, `parseURLPath` and `getIDs` before you trust any version of this.

---

## Tests

`tests/test_patterns.py` is stdlib `unittest`, no dependencies. It asserts that every entry compiles, that names are unique, and that all 44 patterns produce the documented result for their three matching and three non-matching examples. If you edit a pattern, run it.

```bash
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
