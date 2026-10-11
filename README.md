# Property address enrichment with APIVex

Look up property addresses with Python or n8n. Keep the original address, returned address, property ID and available details in a structured result.

[Get an APIVex API key](https://apivex.com/sign-up?utm_source=github&utm_medium=example&utm_campaign=property-address-enrichment) · [API reference](https://apivex.com/docs/zillow?utm_source=github&utm_medium=example&utm_campaign=property-address-enrichment)

## Python quick start

Python 3.10+; no packages required. Download enrich.py and addresses.csv into the same folder. Set your own APIVex API key in your environment.

macOS / Linux:

```sh
export APIVEX_API_KEY="YOUR_KEY"
python3 enrich.py addresses.csv results.csv --limit 10
```

Windows PowerShell:

```powershell
$env:APIVEX_API_KEY="YOUR_KEY"
python enrich.py addresses.csv results.csv --limit 10
```

The CSV needs an address column. Quote addresses containing commas. Existing output files are not overwritten. Duplicate addresses reuse a result within a run. The default limit is 10 input rows. Network failures, HTTP 429 and server errors are retried up to twice; retries may consume quota. Authentication failures and exhausted rate limits stop the run and preserve partial output.

## n8n quick start

1. Import n8n-workflow.json using Import from File.
2. Create the credential below, then click Execute workflow to open the upload form.
3. Create a Header Auth credential with header name x-apivex-key and your APIVex key as its value. Select it in Look up property.
4. Upload a CSV with an address column or a JSON array of strings / objects with an address field. Click Enrich addresses.
5. Inspect Extract addresses and Review results. Download property-results.csv from the binary output of Export results CSV.

Requires n8n 2.42.6+ and a signed-in n8n user with workflow execute permission. Uses built-in nodes. There is no fixed row cap. Exact duplicate addresses are removed before requesting data. Plan quota, file size, n8n memory and execution timeouts limit practical batch size. The whole file is validated before requests begin. Requests run sequentially, with a two-second pause after each lookup. There is no schedule or automatic retry. Review error rows before rerunning.

## Output and limitations

- A returned record is not a verified address match. Compare input_address and returned_address; match_review remains required.
- Unexpected response shapes and multiple results are flagged rather than selecting an arbitrary match.
- Missing values stay blank. A zero price is preserved, but does not mean a home is free. Read home_status and currency with price.
- Zestimate and rental estimates are source-provided estimates, not guaranteed sale prices or income.
- APIVex is a third-party service, not an official Zillow API. API access requires an APIVex key and consumes your plan allowance. RapidAPI credentials do not work with this example's APIVex base URL.

## Working with an AI assistant

Ask it to adapt the CSV input/output while retaining status checks, bounded retries, rate limiting and address review. Keep your key in the environment or n8n credentials, outside the script and workflow export.

## License

The example code is provided under the MIT license. This license covers the example code only; it does not grant rights to underlying property data or change API subscription terms.
