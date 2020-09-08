# Revisions copyright 2020 Joao Rodrigues. All rights reserved.
#
# This file is part of the Biopython distribution and governed by your
# choice of the "Biopython License Agreement" or the "BSD 3-Clause License".
# Please see the LICENSE file that should have been included as part of this
# package.

"""Unit tests for disordered atoms in the Bio.PDB module."""

import os
import tempfile
import unittest
import warnings

import numpy as np

from Bio.PDB import PDBParser, PDBIO
from Bio.PDB.Atom import DisorderedAtom


class TestDisordered(unittest.TestCase):
    """Tests for operations on DisorderedEntities."""

    @classmethod
    def setUpClass(cls):
        cls.parser = parser = PDBParser(QUIET=1)
        cls.structure = parser.get_structure("x", "PDB/disordered.pdb")

    def unpack_all_atoms(self, structure):
        """Return a list of all atoms in the structure."""
        return [a for r in structure.get_residues() for a in r.get_unpacked_list()]

    def test_copy_disordered_atom(self):
        """Copies disordered atoms and all their children."""
        resi27 = self.structure[0]["A"][27]
        resi27_copy = resi27.copy()

        self.assertNotEqual(id(resi27), id(resi27_copy))  # did we really copy

        resi27_atoms = resi27.get_unpacked_list()
        resi27_copy_atoms = resi27.get_unpacked_list()
        self.assertEqual(len(resi27_atoms), len(resi27_copy_atoms))

        for ai, aj in zip(resi27_atoms, resi27_copy_atoms):
            self.assertEqual(ai.name, aj.name)

    def test_copy_entire_chain(self):
        """Copy propagates throughout SMCRA object."""
        s = self.structure
        s_copy = s.copy()

        self.assertNotEqual(id(s), id(s_copy))  # did we really copy

        atoms = self.unpack_all_atoms(s)
        copy_atoms = self.unpack_all_atoms(s_copy)
        self.assertEqual(len(atoms), len(copy_atoms))

        for ai, aj in zip(atoms, copy_atoms):
            self.assertEqual(ai.name, aj.name)

    def test_transform_disordered(self):
        """Transform propagates through disordered atoms."""
        # This test relates to issue #455 where applying a transformation
        # to a copied structure did not work for disordered atoms.
        s = self.structure
        s_copy = s.copy()

        mtx = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        tr_vec = (20.0, 0.0, 0.0)

        s_copy.transform(mtx, tr_vec)  # transform copy

        atoms = self.unpack_all_atoms(s)
        copy_atoms = self.unpack_all_atoms(s_copy)
        self.assertEqual(len(atoms), len(copy_atoms))
        for ai, aj in zip(atoms, copy_atoms):
            self.assertEqual(ai - aj, 20.0)  # check distance == 20.0

    def test_copy_and_write_disordered(self):
        """Extract, save, and parse again disordered atoms."""
        writer = PDBIO()

        s = self.structure

        # Extract the chain object
        chain = s[0]["A"]

        writer.set_structure(chain)

        filenumber, filename = tempfile.mkstemp()  # save to temp file
        os.close(filenumber)
        try:
            writer.save(filename)

            # Parse again
            s2 = self.parser.get_structure("x_copy", filename)

            # Do we have the same stuff?
            atoms1 = self.unpack_all_atoms(s)
            atoms2 = self.unpack_all_atoms(s2)
            self.assertEqual(len(atoms1), len(atoms2))
            for ai, aj in zip(atoms1, atoms2):
                self.assertEqual(ai.name, aj.name)

        finally:
            os.remove(filename)

    # DisorderedAtom.center_of_mass
    def test_structure_w_disordered_com(self):
        """Calculate center of mass of structure including DisorderedAtoms."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = self.parser.get_structure("b", "PDB/disordered.pdb")

        com = s.center_of_mass()

        self.assertTrue(np.allclose(com, [54.545, 19.868, 31.212], atol=1e-3))

    def test_disordered_cog(self):
        """Calculate DisorderedAtom center of geometry."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = self.parser.get_structure("b", "PDB/disordered.pdb")

        arg27 = s[0]["A"][27]

        # Detach all children but NH1
        for atom in list(arg27):
            if atom.name != "NH1":
                arg27.detach_child(atom.name)

        res_cog = arg27.center_of_mass()
        self.assertTrue(np.allclose(res_cog, [59.555, 21.033, 25.954], atol=1e-3))

        # Now compare to DisorderedAtom.center_of_mass
        da_cog = arg27["NH1"].center_of_mass()
        self.assertTrue(np.allclose(res_cog, da_cog, atol=1e-3))

    def test_empty_disordered(self):
        """Raise ValueError on center of mass calculation of empty DisorderedAtom."""
        da = DisorderedAtom("dummy")
        with self.assertRaises(ValueError):
            da.center_of_mass()


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
