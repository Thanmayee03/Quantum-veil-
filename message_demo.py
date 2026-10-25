# QUANTUM VEIL - Message Security Demo

print("\n" + "=" * 55)
print("                 ⚛️ QUANTUM VEIL")
print("=" * 55)

# Sam enters a message
message = input("\n👤 Sam, enter your message: ")

# Ask whether Eve is attacking
attack = input("\n🕵️ Is Eve attacking? (yes/no): ").lower()

print("\n" + "-" * 55)
print("⚛️ QUANTUM SECURITY CHECK...")
print("-" * 55)

if attack == "yes":

    # Simulated compromised channel
    qber = 25.0
    threshold = 11.0

    print(f"\n📊 QBER: {qber}%")
    print(f"🎯 Threshold: {threshold}%")

    if qber > threshold:

        print("\n🚨 INTRUSION DETECTED!")
        print("🕵️ Possible eavesdropper: Eve")
        print("🔐 Quantum key: REJECTED")
        print("🛑 Message: BLOCKED")

        print("\n👤 Riya receives:")
        print("🚨 SECURITY ALERT")
        print("Possible interception detected.")
        print("The message has been blocked.")
        print("Your original message was NOT delivered.")

else:

    # Simulated secure channel
    qber = 0.0
    threshold = 11.0

    print(f"\n📊 QBER: {qber}%")
    print(f"🎯 Threshold: {threshold}%")

    print("\n🟢 CHANNEL SECURE")
    print("🔐 Quantum key: ACCEPTED")
    print("📨 Message: DELIVERED")

    print("\n👤 Riya receives:")
    print("💬", message)

print("\n" + "=" * 55)