# NGC Certificate Import - Implementation Notes

## Status

The NGC certificate import endpoint has been implemented at `/api/v2/import/from-ngc`.

## Current Limitation

**NGC uses strong anti-bot protection (likely Cloudflare)** that blocks automated access even with Playwright. This is a common issue with modern websites that use advanced bot detection.

### What Works
- ✅ Endpoint is correctly implemented
- ✅ Certificate number validation (supports formats like `2167888-014` or `2167888014`)
- ✅ Error handling for all edge cases
- ✅ Response format matches frontend expectations
- ✅ Duplicate detection by certification number

### What's Blocked
- ❌ Automated fetching from NGC website (403 Forbidden)
- This affects both httpx and Playwright-based approaches

## Workarounds

1. **Manual Entry**: Users can manually enter coin data when automated lookup is blocked
2. **Direct URL Access**: Users can visit the NGC certificate page directly:
   - Format: `https://www.ngccoin.com/certlookup/{cert_number}/NGCAncients/`
   - Example: `https://www.ngccoin.com/certlookup/2167888-014/NGCAncients/`

## Future Improvements

If automated access becomes necessary, consider:
1. Using a proxy service that handles Cloudflare bypass
2. Using a headless browser service (e.g., ScrapingBee, Bright Data)
3. Implementing a manual import flow where users paste HTML content
4. Using NGC's official API if available (check with NGC)

## Testing

To test the endpoint (when not blocked):

```bash
curl -X POST http://localhost:8000/api/v2/import/from-ngc \
  -H "Content-Type: application/json" \
  -d '{"cert_number": "2167888-014"}'
```

## Error Codes

- `invalid_cert` - Invalid certificate format
- `not_found` - Certificate not found in NGC database
- `timeout` - Request timed out
- `rate_limit` - Rate limited by NGC
- `anti_bot_blocked` - Blocked by anti-bot protection (403)
- `ngc_error` - Other NGC-related error
