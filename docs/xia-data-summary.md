# Summary of Summer 2024 Super Dataset

Data collected during 07 and 08 2024

## July Data

2024-07...
- 22
- 23
- 24
- 25
- 26
- 30
- 31

2024-08...
- 05
- 06
- [07](<#2024-08-07>): Corrupt
    - Data is not readable
- 09
- 10
- 11
- 12
- 13

### 2024-08-06

Several sets exist in this data, but are only one file long.

### 2024-08-07

The data is LM11 but with TRACELEN=0 we cannot easily calculate the length between traces. There is some data that appears in a binary viewer to look like some trace data, but we would need a new binary processor that sought `eeee`s to find where events began in order to process this data. It is unlikely the data is sufficently valuable to warrant that investment.

Yeah, I found the `EEEE`'s and the result is nothing. Useless :(