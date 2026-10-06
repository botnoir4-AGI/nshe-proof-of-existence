# AetharShield Protocol Specification v1.0

## Post-Quantum Cryptographic Identity & Integrity Protocol

### Parameters
- Dimension (n): 1024 | Modulus (q): 12289 | Module Rank (k): 4 | Total Dim: 4096
- Error: Discrete Gaussian sigma=1.6 | Secret: Dense ternary {-1,0,1}^n

### Key Generation
A <- Z_q^(nxn), s <- chi_ternary^n, e <- chi_gaussian^n, t = (A*s + e) mod q
Public Key: pk=(A,t) | Private Key: sk=s

### Encryption (Bit)
r <- chi_ternary^n, e1 <- chi_gaussian^n, e2 <- chi_gaussian
u = (A^T * r + e1) mod q, v = (t^T * r + e2 + floor(q/2)*m) mod q

### Decryption
w = (v - s^T * u) mod q. If |w| < q/4 or |w-q| < q/4: m=0, else m=1

### Dynamic Permutation Layer (DPL)
Post-encryption Fisher-Yates shuffle with ChaCha8Rng(seed). Reversible with same seed.

### Identity Signing
sign(msg): hash=SHA256(msg)[:8]->int, bit=hash%2, encrypt bit, DPL(u,seed)
Signature: {sig_v: v, hash_mod2: bit, timestamp: ISO8601}

### Lineage Hash Chain
Entry_n = {type, timestamp, data, prev_hash, entry_hash: SHA256(all), signature}
Verify: walk chain, check each hash link + signature.

### Security: Quantum-resistant (Module-LWE), forward-secret (ephemeral DPL), tamper-evident (hash chain), zero external deps.
