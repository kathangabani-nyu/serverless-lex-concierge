# Cleanup Scripts

Scripts to remove AWS resources and manage costs.

## Scripts

### `cleanup-resources.py`
- Removes all created AWS resources
- Helps avoid unexpected charges
- Can be run after assignment completion

### `monitor-costs.py`
- Monitors AWS billing
- Sends alerts for high usage
- Helps manage costs during development

## Usage

```bash
# Clean up all resources
python cleanup-resources.py

# Monitor costs
python monitor-costs.py
```

## Important

Always run cleanup scripts after completing your assignment to avoid ongoing charges!
