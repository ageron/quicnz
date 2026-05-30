# Examples

These scripts demonstrate how to use the `quicnz` library.

## API key setup

The examples read your Quic API key from `~/.quicnz_api.key`.

1. Log in to the [Quic portal](https://account.quic.nz/), select a service, navigate to the bottom of the page, below your product details, and you should find your API key. If the field is empty, click "Roll API Key" to generate the key.

2. Save it to the key file:

   ```bash
   echo "YOUR_API_KEY" > ~/.quicnz_api.key
   ```

3. Make sure to restrict permissions so only your user can read it:

   ```bash
   chmod og-rwx ~/.quicnz_api.key
   ```

## Running the examples

Install the library first:

```bash
pip install quicnz
```

Then run any example directly:

```bash
python examples/list_services.py
python examples/session_status.py                 # uses your first service
python examples/session_status.py service123      # specify a service ID
python examples/download_weathermap.py            # saves weathermap.jpg (website source by default)
python examples/download_weathermap.py --source api  # use API source
python examples/download_weathermap.py ~/map.jpg  # custom output path
python examples/download_weathermap.py --wait-minutes 6  # wait for next regeneration window
```
