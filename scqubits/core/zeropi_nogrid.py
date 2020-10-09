# zeropi.py
#
# This file is part of scqubits.
#
#    Copyright (c) 2019, Jens Koch and Peter Groszkowski
#    All rights reserved.
#
#    This source code is licensed under the BSD-style license found in the
#    LICENSE file in the root directory of this source tree.
############################################################################

import os

import numpy as np
import scipy as sp

import scqubits.core.operators as op
import scqubits.core.qubit_base as base
import scqubits.io_utils.fileio_serializers as serializers


# -Symmetric 0-pi qubit, phi harmonic oscillator, theta in charge basis------------------------------------------------

class ZeroPiNoGrid(base.QubitBaseClass, serializers.Serializable):
    def __init__(self, EJ, EL, ECJ, EC, ng, flux, phi_cutoff, ncut, dEJ=0, dCJ=0, truncated_dim=None):
        self.EJ = EJ
        self.EL = EL
        self.ECJ = ECJ
        self.EC = EC
        self.ECS = 1 / (1 / EC + 1 / ECJ)
        self.dEJ = dEJ
        self.dCJ = dCJ
        self.ng = ng
        self.flux = flux
        self.phi_cutoff = phi_cutoff
        self.ncut = ncut
        self.truncated_dim = truncated_dim
        self._sys_type = type(self).__name__
        self._evec_dtype = np.complex_
        self._image_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qubit_pngs/zeropi.png')

    @staticmethod
    def default_params():
        return {
            'EJ': 10.0,
            'EL': 0.04,
            'ECJ': 20.0,
            'EC': 0.04,
            'dEJ': 0.0,
            'dCJ': 0.0,
            'ng': 0.1,
            'flux': 0.23,
            'ncut': 30,
            'phi_cutoff': 100,
            'truncated_dim': 10
        }

    @staticmethod
    def nonfit_params():
        return ['ng', 'flux', 'ncut', 'phi_cutoff', 'truncated_dim']

    def hilbertdim(self):
        """Returns Hilbert space dimension"""
        return self.phi_cutoff * (2 * self.ncut + 1)

    def E_phi_osc(self):
        return np.sqrt(8.0 * self.ECJ * self.EL)  # since H_harm_phi = 2E_{CJ}n_{\phi}^2 + E_{L}\phi^2

    def phi_osc(self):
        return (2.0 * self.ECJ / self.EL) ** 0.25  # since H_harm_phi = 2E_{CJ}n_{\phi}^2 + E_{L}\phi^2

    def phi_operator(self):
        dimension = self.phi_cutoff
        return (op.creation(dimension) + op.annihilation(dimension)) * self.phi_osc() / np.sqrt(2.)

    def n_phi_operator(self):
        dimension = self.phi_cutoff
        return 1j * (op.creation(dimension) - op.annihilation(dimension)) / (self.phi_osc() * np.sqrt(2.))

    def exp_i_phi_operator(self):
        exponent = 1j * self.phi_operator()
        return sp.linalg.expm(exponent)

    def exp_i_theta_operator(self):
        dimension = 2 * self.ncut + 1
        entries = np.repeat(1.0, dimension - 1)
        exp_op = np.diag(entries, -1)
        return exp_op

    def cos_theta_operator(self):
        return 0.5 * (self.exp_i_theta_operator() + self.exp_i_theta_operator().conj().T)

    def hamiltonian(self):
        identity_phi = np.eye(self.phi_cutoff, dtype=np.complex_)
        identity_theta = np.eye(2 * self.ncut + 1, dtype=np.complex_)

        phi_harmonic = np.diag([i * self.E_phi_osc() for i in range(self.phi_cutoff)])
        theta_kinetic = 2.0 * self.ECS * np.diag(np.square(np.arange(-self.ncut + self.ng, self.ncut + 1 + self.ng)))

        exp_i_phi = self.exp_i_phi_operator()
        cos_phi = 0.5 * (np.exp(-1j*2.0*np.pi*self.flux/2.) * exp_i_phi
                         + np.exp(1j*2.0*np.pi*self.flux/2.) * exp_i_phi.conj().T)
        potential = 2. * self.EJ * (np.kron(identity_phi, identity_theta) - np.kron(cos_phi, self.cos_theta_operator()))

        hamiltonian = (np.kron(phi_harmonic, identity_theta) + np.kron(identity_phi, theta_kinetic)
                       + potential + 0.5 * self.E_phi_osc()*np.kron(identity_phi, identity_theta))
        return hamiltonian