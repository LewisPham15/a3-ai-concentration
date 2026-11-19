# AI provenance matrix

| Artefact | Who | Tool | What was asked | What came back | How it was verified | Outcome |
|---|---|---|---|---|---|---|
| Panel 1  | Tahreema Rahman Zariyat | | | | | |
| Panel 2  | Mohit Sehrawat | | | | | |
| Panel 3 | Eva Shrestha | Claude | Explain the assignment steps and review the Panel 3 code | Reviewed code for panel 3 charts: a 100% stacked column chart by sector, a top 10 organisations bar chart, KPI cards | Recounted 2024 in Excel from the raw CSV: 81 of 98 models were industry only, which is 82.7%, the same as the chart and `panel3_sector_share.csv`. Also ran the app to check it worked. | Improved code and charts for Panel 3  |
| Panel 4 | Ngoc Gia Phong Pham | Claude | Build the disclosure panel: split each year's models by what is known about their training compute, and rank organisations by how often they report one | A stacked area of four confidence bands per year, a share-versus-count control, a January-to-June filter, and a horizontal bar ranking organisations since 2022 | Summed the four band values for every year and compared the total against 100. Six of the ten years came to 100.1 because each band had been rounded on its own, so a 100 per cent stacked area did not close. Also recomputed the caption's "5 of 84 models for 2026" by filtering the source CSV to 2026, then to a non-empty compute figure, then to Confident | Defect fixed by computing the last band as the remainder rather than rounding it independently; every year now sums to exactly 100, and the caption figure reproduces from the raw file |
