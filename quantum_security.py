from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random

# Number of qubits
N = 100

# Security threshold
THRESHOLD = 11

simulator = AerSimulator()

# ==================================================
# SAM
# ==================================================

sam_bits = [random.randint(0, 1) for _ in range(N)]
sam_bases = [random.randint(0, 1) for _ in range(N)]

# ==================================================
# EVE
# ==================================================

eve_bases = [random.randint(0, 1) for _ in range(N)]

# ==================================================
# RIYA
# ==================================================

riya_bases = [random.randint(0, 1) for _ in range(N)]

eve_results = []
riya_results = []

# ==================================================
# QUANTUM COMMUNICATION
# ==================================================

for i in range(N):

    # Sam prepares the qubit
    circuit = QuantumCircuit(1, 1)

    if sam_bits[i] == 1:
        circuit.x(0)

    if sam_bases[i] == 1:
        circuit.h(0)

    # Eve intercepts the qubit
    if eve_bases[i] == 1:
        circuit.h(0)

    circuit.measure(0, 0)

    result = simulator.run(circuit, shots=1).result()
    counts = result.get_counts()

    eve_bit = int(list(counts.keys())[0])
    eve_results.append(eve_bit)

    # ==================================================
    # EVE RESENDS THE QUBIT
    # ==================================================

    resend = QuantumCircuit(1, 1)

    if eve_bit == 1:
        resend.x(0)

    if eve_bases[i] == 1:
        resend.h(0)

    # Riya measures
    if riya_bases[i] == 1:
        resend.h(0)

    resend.measure(0, 0)

    result = simulator.run(resend, shots=1).result()
    counts = result.get_counts()

    riya_bit = int(list(counts.keys())[0])
    riya_results.append(riya_bit)


# ==================================================
# FIND MATCHING BASES
# ==================================================

matching_positions = []

for i in range(N):

    if sam_bases[i] == riya_bases[i]:
        matching_positions.append(i)


# ==================================================
# CALCULATE QBER
# ==================================================

errors = 0

for i in matching_positions:

    if sam_bits[i] != riya_results[i]:
        errors += 1


if len(matching_positions) > 0:
    qber = (errors / len(matching_positions)) * 100
else:
    qber = 0


# ==================================================
# SECURITY DECISION
# ==================================================

print("\n" + "=" * 55)
print("                 ⚛️ QUANTUM VEIL")
print("=" * 55)

print("\n👤 SAM")
print("     ↓")

print("⚛️  QUANTUM CHANNEL")
print("     ↓")

print("🕵️ EVE INTERCEPTS")
print("     ↓")

print("👤 RIYA")

print("\n" + "-" * 55)

print(f"📡 Qubits transmitted : {N}")
print(f"🔗 Matching bases    : {len(matching_positions)}")
print(f"❌ Errors detected   : {errors}")
print(f"📊 QBER              : {qber:.2f}%")
print(f"🎯 Threshold         : {THRESHOLD}%")

print("-" * 55)

if qber > THRESHOLD:

    print("\n🚨 INTRUSION DETECTED!")
    print("🕵️ Possible eavesdropper: EVE")
    print("🔐 QUANTUM KEY: REJECTED")
    print("🛑 MESSAGE: BLOCKED")

else:

    print("\n🟢 CHANNEL SECURE")
    print("🔐 QUANTUM KEY: ACCEPTED")
    print("📨 MESSAGE: ALLOWED")

print("\n" + "=" * 55)

