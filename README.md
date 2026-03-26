# David MacKay Tributes

Static site generator for the David MacKay tribute website.

The site is built from a local [`tributes.csv`](/Users/saw/dev/mackay_tributes/tributes.csv) file plus templates and assets under [`src/`](/Users/saw/dev/mackay_tributes/src). The build output is written to [`dist/`](/Users/saw/dev/mackay_tributes/dist).

## Build

Run:

```bash
python3 tools/build.py
```

By default, the build script first refreshes [`tributes.csv`](/Users/saw/dev/mackay_tributes/tributes.csv) from the published Google Sheet CSV feed for the `Output_for_publishing` tab, then generates the site from the resulting local CSV.

tributes.csv is in git, so you can use that to review differences that were fetched.

If you want to build from the existing local CSV without fetching from Google, run:

```bash
python3 tools/build.py --no-update-tributes-csv
```

If category intro markdown files are missing, the build will fetch them automatically. To force a refresh from Pilgrim's originals during the build, run:

```bash
python3 tools/build.py --download-category-intros
```

These options can be combined.

## Data Source

The tributes data ultimately comes from this Google Sheet tab:

- `Output_for_publishing`
- Spreadsheet: [Google Sheet](https://docs.google.com/spreadsheets/d/1kfNfvsj9qKEja6OShtxYumwcMZWmeYrf9DQmituUgvQ/edit?gid=45077070#gid=45077070)

The build currently reads from the sheet's published CSV endpoint, updates the local [`tributes.csv`](/Users/saw/dev/mackay_tributes/tributes.csv), and then continues using that file for generation. This means the local CSV remains a usable fallback if the online fetch is unavailable or undesirable.

## Deploy

[`deploy.sh`](/Users/saw/dev/mackay_tributes/deploy.sh) contains the current deployment command.
