# OCR Installation Guide

## Overview

This guide provides instructions for installing Tesseract OCR, which is required for processing scanned PDFs in the PDF Editor application.

## Windows Installation

### Option 1: Using Installer (Recommended)

1. **Download Tesseract**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-v5.x.x.exe`)

2. **Run Installer**
   - Double-click the downloaded installer
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\Tesseract-OCR`)
   - Complete the installation

3. **Add to System PATH**
   - Right-click "This PC" → Properties → Advanced → Environment Variables
   - Under "System variables", add new variable:
     - Variable name: `TESSDATA_PREFIX`
     - Variable value: `C:\Program Files\Tesseract-OCR`
   - Add to PATH:
     - Variable name: `Path`
     - Variable value: `C:\Program Files\Tesseract-OCR`
   - Click OK on all dialogs
   - **Restart your computer** to apply changes

4. **Verify Installation**
   - Open Command Prompt (cmd)
   - Run: `tesseract --version`
   - You should see version information (e.g., `tesseract 5.3.0`)

### Option 2: Using Chocolatey

If you have Chocolatey package manager installed:

```cmd
choco install tesseract
```

### Option 3: Using Scoop

If you have Scoop package manager installed:

```cmd
scoop install tesseract
```

## Linux Installation

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

### Fedora/RHEL/CentOS

```bash
sudo dnf install tesseract
sudo dnf install tesseract-devel
```

### Arch Linux

```bash
sudo pacman -S tesseract
```

## macOS Installation

### Using Homebrew (Recommended)

```bash
brew install tesseract
```

### Using MacPorts

```bash
sudo port install tesseract
```

## Language Data Installation

After installing Tesseract, you may need to install language data files for OCR in different languages.

### English (already included)
- English language data is typically included with Tesseract

### Portuguese

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr-por

# macOS (Homebrew)
brew install tesseract-lang

# Windows
# Download from: https://github.com/tesseract-ocr/tessdata
# Extract to: C:\Program Files\Tesseract-OCR\tessdata
```

### Other Languages

Available language data files can be found at:
https://github.com/tesseract-ocr/tessdata

Common language codes:
- `eng` - English
- `por` - Portuguese
- `spa` - Spanish
- `fra` - French
- `deu` - German
- `ita` - Italian
- `rus` - Russian
- `chi_sim` - Chinese Simplified
- `jpn` - Japanese
- `kor` - Korean

## Python Dependencies

Install the required Python packages:

```bash
pip install pytesseract
```

Or using requirements.txt:

```bash
pip install -r requirements.txt
```

## Verification

After installation, verify that everything is working:

### 1. Verify Tesseract Installation

```bash
tesseract --version
```

Expected output:
```
tesseract 5.3.0
 leptonica-1.07.20191014
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.0.2) : libpng 1.6.37 : libtiff 4.0.10 : zlib 1.2.11 : libwebp 0.6.1 : libopenjp2 2.3.1 : libwebpmux 0.5.0 : libwebpdemux 0.6.0 : libwebpdecoder 0.6.1 : libxml2 2.9.4 : libarchive-cmdline 3.0.1 : liblzma 5.2.1 : libzstd 1.5.0 : libzstd 1.5.2
```

### 2. Verify Python Package

```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

Expected output:
```
tesseract 5.3.0
```

### 3. Test OCR

Create a simple test script:

```python
import pytesseract
from PIL import Image

# Create a simple test image
img = Image.new('RGB', (200, 100), color='white')
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)
draw.text((10, 50), "Hello World", fill='black')
img.save('test.png')

# Test OCR
text = pytesseract.image_to_string(img)
print(f"OCR Result: {text}")
```

## Troubleshooting

### Issue: "tesseract is not recognized as an internal or external command"

**Solution:** Add Tesseract to your system PATH (see installation instructions above).

### Issue: "FileNotFoundError: [WinError 2] The system cannot find the file specified"

**Solution:** 
- Verify Tesseract installation directory is correct
- Check PATH environment variable
- On Windows, ensure you're using the correct executable name: `tesseract.exe`

### Issue: "TesseractNotFoundError: tesseract is not installed or it's not in your PATH"

**Solution:**
- Install Tesseract (see installation instructions above)
- Restart your IDE/terminal after installation
- Verify PATH is set correctly

### Issue: "ImportError: No module named 'pytesseract'"

**Solution:**
```bash
pip install pytesseract
```

### Issue: OCR produces poor results

**Possible causes and solutions:**

1. **Image quality too low**
   - Increase DPI in OCR settings (300-400 DPI recommended)
   - Enable image preprocessing (deskew, denoise)

2. **Wrong language**
   - Ensure correct language is selected in OCR configuration
   - Install required language data files

3. **Complex document**
   - Try processing page by page instead of entire document
   - Adjust confidence threshold

4. **Scanned document with poor quality**
   - Preprocess images before OCR
   - Consider using higher quality scans

## Configuration in PDF Editor

After installation, configure OCR in the PDF Editor:

1. **Open PDF Editor**
2. **Click "⚙️ OCR Config" button in toolbar**
3. **Select your preferred settings:**
   - Language: Choose from dropdown (e.g., "eng+por" for English + Portuguese)
   - Quality: Fast, Medium, or High
   - DPI: 150-600 (higher = better accuracy but slower)
   - Preprocessing: Enable/disable deskew, denoise, contrast enhancement
   - Confidence Threshold: 0-100% (text blocks below this are ignored)

4. **Click "Detect Available Languages"** to see all installed language codes

5. **Click "Apply"** to save settings

## Performance Tips

- **For fast processing**: Use "Fast" quality preset with 150 DPI
- **For best accuracy**: Use "High" quality preset with 400-600 DPI
- **For mixed documents**: Use "Medium" quality preset with 300 DPI (good balance)
- **Large documents**: Process page-by-page to avoid memory issues
- **Multi-language documents**: Use combined language codes (e.g., "eng+por")

## Additional Resources

- **Tesseract GitHub**: https://github.com/tesseract-ocr/tesseract
- **Tesseract Wiki**: https://github.com/tesseract-ocr/tesseract/wiki
- **pytesseract Documentation**: https://pypi.org/project/pytesseract/
- **Language Data**: https://github.com/tesseract-ocr/tessdata

## Support

If you encounter issues not covered in this guide:

1. Check the [Tesseract GitHub Issues](https://github.com/tesseract-ocr/tesseract/issues)
2. Check the [pytesseract Issues](https://github.com/madmaze/pytesseract/issues)
3. Review the PDF Editor application logs for specific error messages
