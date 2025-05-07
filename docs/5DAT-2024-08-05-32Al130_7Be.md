# Project <insert name>

## Dataset structure

- All inputs (i.e. building blocks from other sources) are located in
  `in/`.
- All custom code is located in `code/`.
- All annexed outputs are located in `out/`.
  - Output from scripts/code.
  - Compiled/binary data is annexed rather than tracked.
  - To placeholder so the path `out/` is registered in git so `datalad run` can work, use a `.gitattributes` file.
