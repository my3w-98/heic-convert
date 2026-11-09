# HEIC Convert

Free, open-source bulk converter for Apple **HEIC / HEIF** photos.

Convert many images at once to **JPEG**, **PNG**, **WebP**, **TIFF**, **BMP**, or **GIF** using a simple Windows GUI.

Maintained by [my3w-98](https://github.com/my3w-98) · **License:** [GNU GPLv3](LICENSE)

**Repository:** https://github.com/my3w-98/heic-convert

## Features

- Bulk convert files or whole folders
- Recursive folder scanning
- Output format and quality controls
- Optional overwrite of existing files
- Optional open in Microsoft Photos when finished

## Requirements

- Windows 10/11
- [Python 3.11+](https://www.python.org/downloads/) (enable **Add python.exe to PATH** when installing)

## Quick start

```bash
git clone https://github.com/my3w-98/heic-convert.git
cd heic-convert
```

Then double-click **`HEIC Convert.bat`**.

The first launch creates a local virtual environment and installs dependencies automatically.

### Manual install

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\pythonw.exe app.py
```

## Project layout

| Path | Purpose |
|------|---------|
| `HEIC Convert.bat` | Windows launcher |
| `app.py` | GUI application |
| `converter/` | Conversion engine |
| `requirements.txt` | Python dependencies |
| `LICENSE` | GNU General Public License v3 |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and pull requests are welcome.

## Security

See [SECURITY.md](SECURITY.md).

## License

Copyright (C) 2026 my3w-98

HEIC Convert is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but **WITHOUT ANY WARRANTY**; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more details.

## Third-party software

This project uses:

- [Pillow](https://python-pillow.org/)
- [pillow-heif](https://github.com/bigcat88/pillow_heif) (libheif)

Those packages remain under their own licenses.
