# QUANTUM VEIL - Security Decision

# QBER received from the quantum communication
qber = 41.67

# Security threshold
THRESHOLD = 11

print("\n" + "=" * 50)
print("              ⚛️ QUANTUM VEIL")
print("=" * 50)

print(f"\n📊 Measured QBER: {qber}%")
print(f"🎯 Security Threshold: {THRESHOLD}%")

if qber <= THRESHOLD:

    print("\n🟢 CHANNEL STATUS: SAFE")
    print("🔐 Quantum key ACCEPTED")
    print("📨 Message can be securely delivered.")

else:

    print("\n🔴 CHANNEL STATUS: COMPROMISED")
    print("🚨 INTRUSION DETECTED")
    print("🕵️ Possible eavesdropper: Eve")
    print("🔐 Quantum key REJECTED")
    print("🛑 Message BLOCKED")

  