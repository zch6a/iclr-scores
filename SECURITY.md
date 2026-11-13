# Security

## What it does

- **What reaches the network, and when.** `iclr-scores build` downloads one file, the pinned version of the ICLR
  dataset from raw.githubusercontent.com (49 MB, a generic User-Agent), checks its size and SHA-256, reads it from a
  temporary file and deletes it; without pyarrow it says so before downloading anything. `odds` and `years` fetch the
  published statistics from the site (23 KB) unless `--stats` names a local file. Nothing else is fetched.
- **What is published.** Counts and rates over groups of papers: by year, by mean score, by topic. No title, author,
  reviewer or paper identifier is read from the dataset or written anywhere (a test checks the built file).
- **The site.** A static page with a Content-Security-Policy that allows only its own script, style and data; all
  text is inserted as text, never as HTML. The calculator runs in the browser; the scores typed are sent nowhere (they
  are kept in the address after `#`, which browsers do not send to the server, so that a link shows the same).
- **The workflow.** The site is built with a read-only token; the job that deploys it runs nothing of the project.
  Actions are pinned to commits; CI installs from the lock file (`--locked`).
- **Dependencies.** numpy at run time; pyarrow only to build (reading the dataset's Parquet file).

## Reporting a vulnerability

Please open a private security advisory on GitHub (Security → Report a vulnerability) rather than a public issue.
