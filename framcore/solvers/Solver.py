import pickle
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path

from framcore import Base, Model
from framcore.solvers import SolverConfig


class Solver(Base, ABC):
    """
    Solver inteface class.

    In FRAM we call energy market models for Solvers. They take a populated Model and configurations from a SolverConfig,
    and transfers this to the solver software. Then it solves the energy market model, and writes results back to the Model.
    """

    _FILENAME_MODEL = "model.pickle"
    _FILENAME_SOLVER = "solver.pickle"

    def solve(self, model: Model) -> None:
        """
        Inititiate the solve.

        It takes the populated Model and configurations from self.SolverConfig, and transfers this to the solver software.
        Then it solves the energy market model, and writes results back to the Model.

        At the end of the solve, the Model (now with results) and the Solver object (with configurations) are pickled to the solve folder.
        - model.pickle can be used to inspect results later.
        - solver.pickle allows reuse of the same solver configurations (with solve_folder set to None to avoid overwriting).
        TODO: Could also pickle the Model before solving, to have a record of the input model.

        """
        self._check_type(model, Model)

        config = self.get_config()

        folder = config.get_solve_folder()

        if folder is None:
            raise ValueError("A folder for the Solver has not been set yet. Use Solver.get_config().set_solve_folder(folder)")

        Path.mkdir(folder, parents=True, exist_ok=True)

        self._solve(folder, model)

        with Path.open(folder / self._FILENAME_MODEL, "wb") as f:
            pickle.dump(model, f)

        c = deepcopy(self)
        c.get_config().set_solve_folder(None)
        with Path.open(folder / self._FILENAME_SOLVER, "wb") as f:
            pickle.dump(c, f)

    @abstractmethod
    def get_config(self) -> SolverConfig:
        """Return the solver's config object."""
        pass

    @abstractmethod
    def _solve(self, folder: Path, model: Model) -> None:
        """Solve the model inplace. Write to folder. Must be implemented by specific solvers."""
        pass
