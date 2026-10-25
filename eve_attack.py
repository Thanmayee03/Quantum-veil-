from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random

# Number of qubits
N = 20

simulator = AerSimulator()

# -----------------------------
# SAM
# -----------------------------

sam_bits = [random.randint(0, 1) for _ in range(N)]
sam_bases = [random.randint(0, 1) for _ in range(N)]

# -----------------------------
# EVE
# -----------------------------

eve_bases = [random.randint(0, 1) for _ in range(N)]

# -----------------------------
# RIYA
# -----------------------------

riya_bases = [random.randint(0, 1) for _ in range(N)]

eve_results = []
riya_results = []

# -----------------------------
# QUANTUM COMMUNICATION
# -----------------------------

for i in range(N):

    # SAM prepares a qubit
    circuit = QuantumCircuit(1, 1)

    if sam_bits[i] == 1:
        circuit.x(0)

    if sam_bases[i] == 1:
        circuit.h(0)

    # EVE measures the qubit
    if eve_bases[i] == 1:
        circuit.h(0)

    circuit.measure(0, 0)

    result = simulator.run(circuit, shots=1).result()
    counts = result.get_counts()

    eve_bit = int(list(counts.keys())[0])
    eve_results.append(eve_bit)

    # --------------------------------
    # EVE RESENDS THE MEASURED STATE
    # --------------------------------

    resend = QuantumCircuit(1, 1)

    if eve_bit == 1:
        resend.x(0)

    if eve_bases[i] == 1:
        resend.h(0)

    # RIYA measures
    if riya_bases[i] == 1:
        resend.h(0)

    resend.measure(0, 0)

    result = simulator.run(resend, shots=1).result()
    counts = result.get_counts()

    riya_bit = int(list(counts.keys())[0])
    riya_results.append(riya_bit)


# -----------------------------
# COMPARE BASES
# -----------------------------

shared_positions = []

for i in range(N):

    if sam_bases[i] == riya_bases[i]:
        shared_positions.append(i)


# -----------------------------
# CALCULATE ERRORS
# -----------------------------

errors = 0

for i in shared_positions:

    if sam_bits[i] != riya_results[i]:
        errors += 1


if len(shared_positions) > 0:
    qber = (errors / len(shared_positions)) * 100
else:
    qber = 0


# -----------------------------
# DISPLAY RESULTS
# -----------------------------

print("\n" + "=" * 50)
print("              ⚛️ QUANTUM VEIL")
print("=" * 50)

print("\n👤 Sam's bits:")
print(sam_bits)

print("\n📡 Sam's bases:")
print(sam_bases)

print("\n🕵️ Eve's bases:")
print(eve_bases)

print("\n👤 Riya's bases:")
print(riya_bases)

print("\n🕵️ Eve's measurements:")
print(eve_results)

print("\n🔐 Riya's measurements:")
print(riya_results)

print("\n" + "-" * 50)

print("📊 Qubits tested:", N)
print("🔗 Matching bases:", len(shared_positions))
print("❌ Errors detected:", errors)
print(f"📈 QBER: {qber:.2f}%")

print("-" * 50)

if qber > 0:
    print("\n🚨 INTRUSION DETECTED!")
    print("🕵️ Possible eavesdropping by Eve.")
    print("🔐 Quantum key should be REJECTED.")
else:
    print("\n✅ NO INTRUSION DETECTED")
    print("🔒 Quantum key appears secure.")
    