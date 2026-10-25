from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Create 1 qubit and 1 classical bit
circuit = QuantumCircuit(1, 1)

# Put the qubit into a superposition
circuit.h(0)

# Measure the qubit
circuit.measure(0, 0)

print("Our first quantum circuit:")
print(circuit)

# Run the quantum simulation
simulator = AerSimulator()
job = simulator.run(circuit, shots=1000)

result = job.result()
counts = result.get_counts()

print("\nQuantum measurement results:")
print(counts)