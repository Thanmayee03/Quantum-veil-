import random

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


# ==========================================
# BB84 QUANTUM KEY DISTRIBUTION SIMULATOR
# ==========================================

def run_bb84(eve_active=False, number_of_qubits=100):

    simulator = AerSimulator()

    # -----------------------------
    # STEP 1: Sam creates random data
    # -----------------------------

    sam_bits = [
        random.randint(0, 1)
        for _ in range(number_of_qubits)
    ]

    sam_bases = [
        random.randint(0, 1)
        for _ in range(number_of_qubits)
    ]

    # Riya randomly chooses measurement bases
    riya_bases = [
        random.randint(0, 1)
        for _ in range(number_of_qubits)
    ]

    # Eve chooses random bases if attacking
    eve_bases = [
        random.randint(0, 1)
        for _ in range(number_of_qubits)
    ]

    riya_results = []

    # ==========================================
    # STEP 2: Quantum transmission
    # ==========================================

    for i in range(number_of_qubits):

        # --------------------------------------
        # SAM PREPARES THE QUBIT
        # --------------------------------------

        circuit = QuantumCircuit(1, 1)

        # Encode Sam's bit
        if sam_bits[i] == 1:
            circuit.x(0)

        # Encode Sam's basis
        # 0 = Z basis
        # 1 = X basis
        if sam_bases[i] == 1:
            circuit.h(0)

        # --------------------------------------
        # EVE INTERCEPTS THE QUBIT
        # --------------------------------------

        if eve_active:

            # Eve measures in her randomly
            # chosen basis.

            if eve_bases[i] == 1:
                circuit.h(0)

            circuit.measure(0, 0)

            result = simulator.run(
                circuit,
                shots=1
            ).result()

            counts = result.get_counts()

            eve_bit = int(
                list(counts.keys())[0]
            )

            # ----------------------------------
            # EVE RESENDS A NEW QUBIT
            # ----------------------------------

            circuit = QuantumCircuit(1, 1)

            if eve_bit == 1:
                circuit.x(0)

            if eve_bases[i] == 1:
                circuit.h(0)

        # --------------------------------------
        # RIYA MEASURES THE QUBIT
        # --------------------------------------

        if riya_bases[i] == 1:
            circuit.h(0)

        circuit.measure(0, 0)

        result = simulator.run(
            circuit,
            shots=1
        ).result()

        counts = result.get_counts()

        riya_bit = int(
            list(counts.keys())[0]
        )

        riya_results.append(riya_bit)

    # ==========================================
    # STEP 3: BASIS SIFTING
    # ==========================================

    matching_positions = [
        i
        for i in range(number_of_qubits)
        if sam_bases[i] == riya_bases[i]
    ]

    # ==========================================
    # STEP 4: QBER CALCULATION
    # ==========================================

    errors = sum(
        1
        for i in matching_positions
        if sam_bits[i] != riya_results[i]
    )

    if matching_positions:

        qber = (
            errors /
            len(matching_positions)
        ) * 100

    else:

        qber = 0

    # ==========================================
    # RETURN RESULTS
    # ==========================================

    return {
        "qubits": number_of_qubits,
        "matching_bases": len(matching_positions),
        "errors": errors,
        "qber": round(qber, 2),
        "eve_active": eve_active
    }


# ==========================================
# TEST THE ENGINE
# ==========================================

if __name__ == "__main__":

    print("\n⚛️ QUANTUM VEIL — BB84 ENGINE")
    print("=" * 45)

    print("\n🟢 NORMAL QUANTUM CHANNEL")

    normal = run_bb84(
        eve_active=False,
        number_of_qubits=100
    )

    print(f"Qubits: {normal['qubits']}")
    print(f"Matching bases: {normal['matching_bases']}")
    print(f"Errors: {normal['errors']}")
    print(f"QBER: {normal['qber']}%")

    print("\n🔴 EVE INTERCEPT-RESEND ATTACK")

    attack = run_bb84(
        eve_active=True,
        number_of_qubits=100
    )

    print(f"Qubits: {attack['qubits']}")
    print(f"Matching bases: {attack['matching_bases']}")
    print(f"Errors: {attack['errors']}")
    print(f"QBER: {attack['qber']}%")  