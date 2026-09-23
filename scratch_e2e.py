import httpx
import time
import json
import nacl.signing

client = httpx.Client(base_url='http://localhost:8000')

# 1. Test Apple Gross Margin (Expected: PASS)
print('--- 1. Testing Apple Gross Margin (Pass Scenario) ---')
res = client.post('/api/v1/verify', json={
    'content': 'In fiscal 2025, Apple reported gross margin of 42.32% based on total net revenues of $4.82B and cost of goods sold of $2.78B.',
    'content_format': 'text',
    'filing_cik': '0000320193',
    'filing_period': '2025-Q4',
    'form_type': '10-K',
    'llm_model': 'gpt-4o'
}).json()
time.sleep(2)
ledger = client.get('/api/v1/ledger').json()
latest = ledger['items'][0]
print('Claim Text:', latest['claim_text'])
print('Status:', latest['status'])
print('Computed Value:', latest['computed_value'], 'Expected Value:', latest['expected_value'])
print('Relative Error:', latest['relative_error'])

# 2. Test Tesla Operating Margin (Expected: FAIL - Hallucination)
print('\n--- 2. Testing Tesla Operating Margin (Hallucination Fail Scenario) ---')
res2 = client.post('/api/v1/verify', json={
    'content': 'Operating margin expanded significantly to 21.0% in 2024 based on total revenues of $96.77B, cost of revenues of $79.11B, and operating expenses of $8.77B.',
    'content_format': 'text',
    'filing_cik': '0001318605',
    'filing_period': '2024-Q4',
    'form_type': '10-K',
    'llm_model': 'gpt-4o'
}).json()
time.sleep(2)
ledger2 = client.get('/api/v1/ledger').json()
latest2 = ledger2['items'][0]
print('Claim Text:', latest2['claim_text'])
print('Status:', latest2['status'])
print('Computed Value:', latest2['computed_value'], 'Expected Value:', latest2['expected_value'])
print('Relative Error:', latest2['relative_error'])

# 3. Test Footnote Unverifiable & Human Review Flow
print('\n--- 3. Testing Footnote Claim & Review Adjudication Flow ---')
res3 = client.post('/api/v1/verify', json={
    'content': 'Adjusted EBITDA reached $14.5B with estimated synthetic synergies of $2.3B across undisclosed business lines.',
    'content_format': 'text',
    'filing_cik': '0000320193',
    'filing_period': '2025-Q4',
    'form_type': '10-K',
    'llm_model': 'gpt-4o'
}).json()
time.sleep(2)
ledger3 = client.get('/api/v1/ledger?status=unverifiable').json()
unverifiable_cert = ledger3['items'][0]
cid = unverifiable_cert['cert_id']
print('Initial Status:', unverifiable_cert['status'])

# Review and accept
rev = client.post(f'/api/v1/review/{cid}', json={
    'reviewer_id': 'senior_auditor',
    'decision': 'accepted',
    'annotation': 'Approved based on footnote schedule 4A.'
}).json()

# Fetch updated certificate
updated_cert = client.get(f'/api/v1/certificates/{cid}').json()
print('Adjudicated Certificate Status:', updated_cert['status'])
print('Reviewer Decision:', updated_cert['reviewer_decision'])
print('Adjudicated Signature (128 chars):', updated_cert['signature'][:32] + '...')

# Verify Adjudicated Certificate Cryptographically
pub_res = client.get('/api/v1/public-key').json()
pub_key = bytes.fromhex(pub_res['public_key'])
sig = bytes.fromhex(updated_cert['signature'])
canonical_bytes = json.dumps(updated_cert['cert_payload_json'], sort_keys=True, separators=(',', ':')).encode('utf-8')
verify_key = nacl.signing.VerifyKey(pub_key)
verify_key.verify(canonical_bytes, sig)
print('\nCryptographic 1-Click Verification of Adjudicated PASS Certificate: VALID & AUTHENTIC!')
