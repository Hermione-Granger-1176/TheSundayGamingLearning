name: Update Content
on:
  push:
    paths:
      - 'sessions/**'
      - 'scripts/**'
      - '.github/workflows/update.yml'
  schedule:
    - cron: '0 0 * * 0'  # Run weekly on Sundays
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-content:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Fetch all history for better caching

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Cache session data
      uses: actions/cache@v3
      with:
        path: .cache
        key: ${{ runner.os }}-session-cache-${{ hashFiles('sessions/**') }}
        restore-keys: |
          ${{ runner.os }}-session-cache-
        
    - name: Generate site
      run: python scripts/generate_sessions.py
      env:
        GITHUB_REPOSITORY: ${{ github.repository }}
        PYTHONUNBUFFERED: 1
        
    - name: Commit changes
      run: |
        git config --global user.name "GitHub Actions"
        git config --global user.email "actions@github.com"
        git remote set-url origin https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
        git add index.md
        git diff --staged --quiet || git commit -m "Auto-update content [skip ci]"
        git push
