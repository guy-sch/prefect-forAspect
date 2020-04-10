import os
from typing import Any

import cloudpickle

from prefect import config
from prefect.engine.result import Result


class LocalResult(Result):
    """
    Result that is written to and retrieved from the local file system.

    Args:
        - value (Any): the underlying value this Result should represent
        - dir (str, optional): the _absolute_ path to a directory for storing
            all results; defaults to `${prefect.config.home_dir}/results`
        - validate_dir (bool, optional): a boolean specifying whether to validate the
            provided directory path; if `True`, the directory will be converted to an
            absolute path and created.  Defaults to `True`
        - **kwargs (Any, optional): any additional `Result` initialization options
    """

    def __init__(
        self,
        value: Any = None,
        dir: str = None,
        validate_dir: bool = True,
        **kwargs: Any
    ) -> None:
        self.value = value

        full_prefect_path = os.path.abspath(config.home_dir)
        if (
            dir is None
            or os.path.commonpath([full_prefect_path, os.path.abspath(dir)])
            == full_prefect_path
        ):
            directory = os.path.join(config.home_dir, "results")
        else:
            directory = dir

        if validate_dir:
            abs_directory = os.path.abspath(os.path.expanduser(directory))
            if not os.path.exists(abs_directory):
                os.makedirs(abs_directory)
        else:
            abs_directory = directory
        self.dir = abs_directory

        super().__init__(value=value, **kwargs)

    def read(self, filepath: str) -> Result:
        """
        Reads a result from the local file system and returns the corresponding `Result` instance.

        Args:
            - filepath (str): the filepath to read from

        Returns:
            - Result: a new result instance with the data represented by the filepath
        """
        new = self.copy()
        new.filepath = filepath

        self.logger.debug("Starting to read result from {}...".format(filepath))

        with open(os.path.join(self.dir, filepath), "rb") as f:
            new.value = cloudpickle.loads(f.read())

        self.logger.debug("Finished reading result from {}...".format(filepath))

        return new

    def write(self, value: Any, **kwargs: Any) -> Result:
        """
        Writes the result to a location in the local file system and returns a new `Result`
        object with the result's filepath.

        Args:
            - value (Any): the value to write; will then be stored as the `value` attribute
                of the returned `Result` instance
            - **kwargs (optional): if provided, will be used to format the filepath template
                to determine the location to write to

        Returns:
            - Result: returns a new `Result` with both `value` and `filepath` attributes
        """
        new = self.format(**kwargs)
        new.value = value

        self.logger.debug("Starting to upload result to {}...".format(new.filepath))

        with open(os.path.join(self.dir, new.filepath), "wb") as f:
            f.write(cloudpickle.dumps(new.value))

        self.logger.debug("Finished uploading result to {}...".format(new.filepath))

        return new

    def exists(self, filepath: str) -> bool:
        """
        Checks whether the target result exists in the file system.

        Does not validate whether the result is `valid`, only that it is present.

        Args:
            - filepath (str): Location of the result in the specific result target.
                Will check whether the provided filepath exists

        Returns:
            - bool: whether or not the target result exists
        """
        return os.path.exists(os.path.join(self.dir, filepath))
