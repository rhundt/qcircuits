import unittest

import copy
import numpy as np
from scipy.stats import unitary_group, dirichlet

import sys
sys.path.append('..')
import qcircuits as qc


epsilon = 1e-10


def max_absolute_difference(T1, T2):
    return np.max(np.abs(T1[:] - T2[:]))


def random_unitary_operator(d):
    num_basis_vectors = 2**d
    M = unitary_group.rvs(num_basis_vectors)
    permute = [0] * 2 * d
    permute[::2] = range(d)
    permute[1::2] = range(d, 2*d)

    return qc.operators.Operator(M.reshape([2] * 2 * d).transpose(permute))


def get_adjoint(Op):
    d = Op.rank // 2
    permute = [0] * 2 * d
    permute[::2] = range(d)
    permute[1::2] = range(d, 2*d)
    matrix_side = 2**d
    M = Op._t.transpose(np.argsort(permute)).reshape(matrix_side, matrix_side)
    M_adj = np.conj(M.T)
    op_shape = [2] * 2 * d
    M_adj = M_adj.reshape(op_shape).transpose(permute)
    return qc.operators.Operator(M_adj)


def random_state(d):
    num_basis_vectors = 2**d
    shape = [2] * d
    real_part = np.sqrt(dirichlet(alpha=[1]*num_basis_vectors).rvs()[0, :])
    imag_part = np.exp(1j * np.random.uniform(0, 2*np.pi, size=num_basis_vectors))
    amplitudes = (real_part * imag_part).reshape(shape)
    return qc.state.State(amplitudes)


def random_boolean_function(d):
    ans = np.random.choice([0, 1], 2**d)

    def f(*bits):
        index = sum(v * 2**i for i, v in enumerate(bits))

        return ans[index]

    return f


class StateUnitLengthTests(unittest.TestCase):
    """
    Test that random or defined states are of unit length.
    """

    def setUp(self):
        self.d_states = [qc.zeros, qc.ones, qc.positive_superposition]

    def test_defined_d_dim_states_unit_length(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            for state_type in self.d_states:
                state = state_type(d=d)
                diff = abs(state.probabilities.sum() - 1)
                self.assertLess(diff, epsilon)

    def test_bell_state_unit_length(self):
        for x, y in product([0, 1], repeat=2):
            state = qc.bell_state(x, y)
            diff = abs(state.probabilities.sum() - 1)
            self.assertLess(diff, epsilon)

    def test_bitstring_state_unit_length(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            bits = np.random.choice([0, 1], size=d)
            state = qc.bitstring(*bits)
            diff = abs(state.probabilities.sum() - 1)
            self.assertLess(diff, epsilon)

    def test_qubit_state_unit_length(self):
        num_tests = 10
        for test_i in range(num_tests):
            theta = np.random.normal(scale=10)
            phi = np.random.normal(scale=10)
            global_phase = np.random.normal(scale=10)
            state = qc.qubit(theta=theta, phi=phi, global_phase=global_phase)
            diff = abs(state.probabilities.sum() - 1)
            self.assertLess(diff, epsilon)

    def test_random_state_unit_length(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            state = random_state(d)
            diff = abs(state.probabilities.sum() - 1)
            self.assertLess(diff, epsilon)

    def test_tensor_product_state_unit_length(self):
        num_tests = 10
        for test_i in range(num_tests):
            d1 = np.random.randint(1, 4)
            d2 = np.random.randint(1, 4)
            state1 = random_state(d1)
            state2 = random_state(d2)
            state = state1 * state2
            diff = abs(state.probabilities.sum() - 1)
            self.assertLess(diff, epsilon)


class StateSwapPermuteTests(unittest.TestCase):
    def test_permute_reverse(self):
        """
        Test that permuting and then reversing the permutation
        results in the original state.
        """

        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 8)
            state = random_state(d)
            indices = np.arange(d)
            np.random.shuffle(indices)
            state_copy = copy.deepcopy(state)
            state.permute_qubits(indices)
            state.permute_qubits(indices, inverse=True)
            diff = max_absolute_difference(state, state_copy)
            self.assertLess(diff, epsilon)

    def test_swap_reverse(self):
        """
        Test that swapping qubits and then swapping back results
        in the original state.
        """

        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 8)
            state = random_state(d)
            i1, i2 = np.random.choice(d, replace=False, size=2)
            state_copy = copy.deepcopy(state)
            state.swap_qubits(i1, i2)
            state.swap_qubits(i1, i2)
            diff = max_absolute_difference(state, state_copy)
            self.assertLess(diff, epsilon)

    def test_operator_sub_application_equivalence_to_perumation(self):
        num_tests = 10
        for test_i in range(num_tests):
            state_d = np.random.randint(3, 8)
            op_d = np.random.randint(2, state_d)
            state1 = random_state(state_d)
            U = random_unitary_operator(op_d)

            application_indices = list(np.random.choice(state_d, replace=False, size=op_d))
            state = copy.deepcopy(state1)
            result1 = U(state, qubit_indices=application_indices)

            non_app_indices = sorted(list(set(range(state_d)) - set(application_indices)))
            permutation = application_indices + non_app_indices
            state = copy.deepcopy(state1)
            state.permute_qubits(permutation)
            result2 = U(state, qubit_indices=range(op_d))
            result2.permute_qubits(permutation, inverse=True)

            diff = max_absolute_difference(result1, result2)
            self.assertLess(diff, epsilon)

    def test_operator_d1_sub_application_equivalence_to_swap(self):
        num_tests = 10
        for test_i in range(num_tests):
            state_d = np.random.randint(3, 8)
            state1 = random_state(state_d)
            U = random_unitary_operator(1)

            application_index = np.random.choice(state_d)
            state = copy.deepcopy(state1)
            result1 = U(state, qubit_indices=[application_index])

            state = copy.deepcopy(state1)
            state.swap_qubits(0, application_index)
            result2 = U(state, qubit_indices=[0])
            result2.swap_qubits(0, application_index)

            diff = max_absolute_difference(result1, result2)
            self.assertLess(diff, epsilon)


class TensorProductTests(unittest.TestCase):
    def test_tensor_product(self):
        """
        Test that (A * B)(x * y) = A(x) * B(y)
        """

        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 6)
            A = random_unitary_operator(d)
            B = random_unitary_operator(d)
            x = random_state(d)
            y = random_state(d)
            R1 = (A * B)(x * y)
            R2 = A(x) * B(y)
            diff = max_absolute_difference(R1, R2)
            self.assertLess(diff, epsilon)


class OperatorIdentitiesTest(unittest.TestCase):

    def setUp(self):
        self.squared_equals_I_list = [
            qc.Hadamard, qc.PauliX, qc.PauliY, qc.PauliZ
        ]

    def test_squared_equals_I(self):
        for Op_type in self.squared_equals_I_list:
            I = qc.Identity()
            U = Op_type()

            diff = max_absolute_difference(U(U), I)
            self.assertLess(diff, epsilon)

    def test_sqrtnot_squared_equals_X(self):
        R1 = qc.SqrtNot()(qc.SqrtNot())
        R2 = qc.PauliX()
        diff = max_absolute_difference(R1, R2)
        self.assertLess(diff, epsilon)

    def test_sqrtswap_squared_equals_swap(self):
        R1 = qc.SqrtSwap()(qc.SqrtSwap())
        R2 = qc.Swap()
        diff = max_absolute_difference(R1, R2)
        self.assertLess(diff, epsilon)


class OperatorUnitaryTests(unittest.TestCase):
    """
    Various tests to test if random or defined operators are unitary.
    """

    def setUp(self):
        self.d_ops = [
            qc.Identity, qc.PauliX, qc.PauliY, qc.PauliZ,
            qc.Hadamard, qc.Phase, qc.SqrtNot
        ]
        self.d_op_names = ['I', 'X', 'Y', 'Z', 'H', 'Phase', 'SqrtNot']
        self.non_d_ops = [
            qc.CNOT, qc.Toffoli, qc.Swap, qc.SqrtSwap
        ]
        self.non_d_op_names = ['CNOT', 'Toffoli', 'Swap', 'SqrtSwap']
        self.non_d_op_dims = [2, 3, 2, 2]

    def test_random_operator_unitary(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 8)
            Op = random_unitary_operator(d)
            Op_adj = get_adjoint(Op)
            I = qc.Identity(d)
            max_diff = max_absolute_difference(Op(Op_adj), I)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(Op_adj(Op), I)
            self.assertLess(max_diff, epsilon)

    def test_random_operator_adjoint_equal_matrix_adjoint(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            U = random_unitary_operator(d)
            U_from_matrix_adjoint = get_adjoint(U)
            U_from_adjoint_property = U.adj
            max_diff = max_absolute_difference(U_from_adjoint_property,
                                               U_from_matrix_adjoint)
            self.assertLess(max_diff, epsilon)

    def test_tensor_product_operator_unitary(self):
        num_tests = 10
        for test_i in range(num_tests):
            d1 = np.random.randint(3, 5)
            d2 = np.random.randint(3, 5)
            d = d1 + d2
            Op1 = random_unitary_operator(d1)
            Op2 = random_unitary_operator(d2)
            Op = Op1 * Op2
            Op_adj = get_adjoint(Op)
            I = qc.Identity(d)
            max_diff = max_absolute_difference(Op(Op_adj), I)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(Op_adj(Op), I)
            self.assertLess(max_diff, epsilon)

    def test_defined_operators_unitary(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 8)
            I = qc.Identity(d)
            for Op_type, op_name in zip(self.d_ops, self.d_op_names):
                Op = Op_type(d=d)
                Op_adj = get_adjoint(Op)
                max_diff = max_absolute_difference(Op(Op_adj), I)
                self.assertLess(max_diff, epsilon)
                max_diff = max_absolute_difference(Op_adj(Op), I)
                self.assertLess(max_diff, epsilon)
        for Op_type, op_name, d in zip(self.non_d_ops, self.non_d_op_names, self.non_d_op_dims):
            Op = Op_type()
            Op_adj = get_adjoint(Op)
            I = qc.Identity(d)
            max_diff = max_absolute_difference(Op(Op_adj), I)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(Op_adj(Op), I)
            self.assertLess(max_diff, epsilon)

    def test_U_f_unitary(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 7)
            f = random_boolean_function(d)
            Op = qc.U_f(f, d=d+1)
            Op_adj = get_adjoint(Op)
            I = qc.Identity(d+1)
            max_diff = max_absolute_difference(Op(Op_adj), I)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(Op_adj(Op), I)
            self.assertLess(max_diff, epsilon)

    def test_ControlledU_unitary(self):
        num_tests = 10
        for test_i in range(num_tests):
            d = np.random.randint(3, 7)
            U = random_unitary_operator(d)
            Op = qc.ControlledU(U)
            Op_adj = get_adjoint(Op)
            I = qc.Identity(d+1)
            max_diff = max_absolute_difference(Op(Op_adj), I)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(Op_adj(Op), I)
            self.assertLess(max_diff, epsilon)


class OperatorCompositionTests(unittest.TestCase):

    def setUp(self):
        self.num_tests = 10
        self.ds = []
        self.U1s = []

        for test_i in range(self.num_tests):
            d = np.random.randint(3, 8)
            U1 = random_unitary_operator(d)
            self.ds.append(d)
            self.U1s.append(U1)

    def test_operator_composition_order(self):
        """
        For two operators U1 and U2, and state x, we should have
        (U1(U2))(x) = U1(U2(x))
        """

        for test_i, (d, U1) in enumerate(zip(self.ds, self.U1s)):
            U2 = random_unitary_operator(d)
            U3 = random_unitary_operator(d)
            x = random_state(d)

            result1 = U1(U2(U3(x)))
            result2 = (U1(U2))(U3(x))
            result3 = (U1(U2(U3)))(x)
            max_diff = max_absolute_difference(result1, result2)
            self.assertLess(max_diff, epsilon)
            max_diff = max_absolute_difference(result1, result3)
            self.assertLess(max_diff, epsilon)

    def test_operator_identity_composition(self):
        """
        The composition of an operator with the identity operator
        should be the same as the original operator.
        """

        for test_i, (d, U) in enumerate(zip(self.ds, self.U1s)):
            I = qc.Identity(d)
            R = I(U(I))

            max_diff = max_absolute_difference(U, R)
            self.assertLess(max_diff, epsilon)


class ApplyingToSubsetsOfQubitsTests(unittest.TestCase):

    def test_application_to_qubit_subset(self):
        """
        Instead of applying the tensor product of the Identity
        operator with another operator to a state, we can apply
        the operator to a subset of axes of the state. We should
        get the same result. We can also permute the order of
        operators in the tensor product, and correspondingly
        permute the application order.
        """

        num_tests = 10
        I = qc.Identity()

        for test_i in range(num_tests):
            d = np.random.randint(3, 8)
            num_apply_to = np.random.randint(2, d)
            apply_to_indices = np.random.choice(d, size=num_apply_to, replace=False)

            M_all = None
            Ops = []
            for qubit_i in range(d):
                if qubit_i in apply_to_indices:
                    Op = random_unitary_operator(d=1)
                else:
                    Op = I
                Ops.append(Op)
                if M_all is None:
                    M_all = Op
                else:
                    M_all = M_all * Op

            M_subset = None
            for apply_to_index in apply_to_indices:
                Op = Ops[apply_to_index]
                if M_subset is None:
                    M_subset = Op
                else:
                    M_subset = M_subset * Op

            x = random_state(d)

            result1 = M_all(x)
            result2 = M_subset(x, qubit_indices=apply_to_indices)
            max_diff = max_absolute_difference(result1, result2)
            self.assertLess(max_diff, epsilon)


class FastMeasurementTests(unittest.TestCase):

    def test_bitstring_measurement(self):
        num_tests = 10

        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            bits = tuple(np.random.choice([0, 1], size=d, replace=True))
            state = qc.bitstring(*bits)
            measurement = state.measure()

            self.assertEqual(bits, measurement)

    def test_repeated_measurement_same(self):
        num_tests = 10

        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            state = random_state(d)
            measurement1 = state.measure(remove=False)
            measurement2 = state.measure(remove=False)

            self.assertEqual(measurement1, measurement2)

    def test_repeated_single_qubit_measurement_same1(self):
        num_tests = 10

        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            state = random_state(d)
            qubit_to_measure = int(np.random.randint(d))

            measurement1 = state.measure(remove=False)[qubit_to_measure]
            measurement2 = state.measure(qubit_indices=qubit_to_measure, remove=False)

            self.assertEqual(measurement1, measurement2)

    def test_repeated_single_qubit_measurement_same2(self):
        num_tests = 10

        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            state = random_state(d)
            qubit_to_measure = int(np.random.randint(d))

            measurement1 = state.measure(qubit_indices=qubit_to_measure, remove=False)
            measurement2 = state.measure(qubit_indices=qubit_to_measure, remove=False)

            self.assertEqual(measurement1, measurement2)

    def test_U_f_basis_measurement(self):
        num_tests = 10

        for test_i in range(num_tests):
            d = np.random.randint(1, 8)
            f = random_boolean_function(d)
            U = qc.U_f(f, d=d+1)
            bits = tuple(np.random.choice([0, 1], size=d, replace=True))
            input_qubits = qc.bitstring(*bits)
            ans_qubit = qc.zeros()
            state = input_qubits * ans_qubit
            state = U(state)

            answer = f(*bits)
            measured_ans = state.measure(qubit_indices=d)

            self.assertEqual(answer, measured_ans)


sys.path.append('../examples')
from itertools import product
from deutsch_algorithm import deutsch_algorithm
import deutsch_jorza_algorithm as dj_algorithm
from quantum_teleportation import quantum_teleportation
from superdense_coding import superdense_coding
import produce_bell_states
import quantum_parallelism

def deutsch_function(L):
    return lambda x: L[x]

class TestExamples(unittest.TestCase):
    """
    Test that the examples work as expected.
    """

    def test_deutsch_algorithm_example(self):
        for i, j in product([0, 1], repeat=2):
            f = deutsch_function([i, j])
            measurement = deutsch_algorithm(f)
            parity = int(i!=j)
            self.assertEqual(measurement, parity)

    def test_deutsch_jorza_algorithm_example(self):
        num_tests = 10
        for problem_type in ['constant', 'balanced']:
            for test_i in range(num_tests):
                d = np.random.randint(3, 8)
                f = dj_algorithm.construct_problem(d, problem_type)
                measurements = dj_algorithm.deutsch_jorza_algorithm(d, f)

                if problem_type == 'constant':
                    self.assertTrue(not(any(measurements)))
                else:
                    self.assertTrue(any(measurements))

    def test_quantum_teleportation_example(self):
        num_tests = 10
        for test_i in range(num_tests):
            alice_state = random_state(d=1)
            bob_state = quantum_teleportation(alice_state)
            diff = max_absolute_difference(alice_state, bob_state)
            self.assertLess(diff, epsilon)

    def test_superdense_coding_example(self):
        num_tests = 10
        for test_i in range(num_tests):
            for bit_1, bit_2 in product([0, 1], repeat=2):
                measurements = superdense_coding(bit_1, bit_2)
                self.assertEqual(bit_1, measurements[0])
                self.assertEqual(bit_2, measurements[1])

    def test_bell_state_example(self):
        for x, y in product([0, 1], repeat=2):
            state1 = qc.bell_state(x, y)
            state2 = produce_bell_states.bell_state(x, y)
            diff = max_absolute_difference(state1, state2)
            self.assertLess(diff, epsilon)

    def test_quantum_parallelism_example(self):
        """
        This test currently just makes sure the example runs
        """

        f = quantum_parallelism.construct_problem()
        quantum_parallelism.quantum_parallelism(f)


if __name__ == '__main__':
    unittest.main()
