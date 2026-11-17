# Unicode fonts and PDF portability (v0.2)

Spek does **not** package or distribute font files. PDF compilation uses installed TrueType pairs instead of silently falling back to ReportLab's WinAnsi Helvetica fonts.

## Automatic discovery

1. Linux: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` and `DejaVuSans-Bold.ttf`.
2. Windows: `%WINDIR%\Fonts\segoeui.ttf` and `segoeuib.ttf`, or Arial (`arial.ttf` and `arialbd.ttf`).
3. macOS: an installed Arial pair, if available.

If no supported fonts exist, PDF builds fail with a clear error. This is deliberate: an apparently successful PDF with substituted scientific symbols is unacceptable.

## Choose your own installed TTF files

PowerShell:

```powershell
$env:SPEK_FONT_REGULAR="C:\Windows\Fonts\segoeui.ttf"
$env:SPEK_FONT_BOLD="C:\Windows\Fonts\segoeuib.ttf"
python -m spek build --out dist --formats html,pdf,tex
```

Bash:

```bash
export SPEK_FONT_REGULAR=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
export SPEK_FONT_BOLD=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
python -m spek build --out dist --formats html,pdf,tex
```

Both variables must be specified together; paths must point to installed `.ttf` files. All characters used by the PDF content and its trace labels are checked against both font character maps. If a glyph is absent, compilation **stops** with an error naming the missing Unicode character(s). This checks coverage, not typography, shaping, or cross-language translation quality. For right-to-left scripts and complex shaping, additional work is required; v0.2 only has tested FR/EN/IT support.

PDF bytes may vary across operating systems and fonts. Build reproducibility is checked **within the same environment**; identical cross-platform binary PDFs are not claimed.

The generated XeLaTeX source searches for DejaVu Sans, then Segoe UI, then Latin Modern Roman. XeLaTeX is optional and must be installed separately to compile `.tex` to PDF.
