from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random

# Number of qubits
N = 20

simulator = AerSimulator()

# Sam randomly chooses bits: 0 or 1
sam_bits = [random.randint(0, 1) for _ in range(N)]

# Sam randomly chooses bases: 0 or 1
sam_bases = [random.randint(0, 1) for _ in range(N)]

# Riya randomly chooses measurement bases
riya_bases = [random.randint(0, 1) for _ in range(N)]

riya_results = []

for i in range(N):

    circuit = QuantumCircuit(1, 1)

    # Sam prepares the qubit
    if sam_bits[i] == 1:
        circuit.x(0)

    # Sam's basis
    if sam_bases[i] == 1:
        circuit.h(0)

    # Riya's basis
    if riya_bases[i] == 1:
        circuit.h(0)

    # Riya measures
    circuit.measure(0, 0)

    result = simulator.run(circuit, shots=1).result()
    counts = result.get_counts()

    measurement = int(list(counts.keys())[0])

    riya_results.append(measurement)


# Keep only matching bases
shared_key = []

for i in range(N):
    if sam_bases[i] == riya_bases[i]:
        shared_key.append(riya_results[i])


print("\n" + "=" * 45)
print("          ⚛️  QUANTUM VEIL")
print("=" * 45)

print("\n👤 Sam's bits:")
print(sam_bits)

print("\n📡 Sam's bases:")
print(sam_bases)

print("\n👤 Riya's bases:")
print(riya_bases)

print("\n🔐 Riya's measurements:")
print(riya_results)

print("\n🔑 SHARED QUANTUM KEY:")
print(shared_key)

print("\n✅ QUANTUM KEY ESTABLISHED")
print("🔒 Sam and Riya can now communicate securely.")
