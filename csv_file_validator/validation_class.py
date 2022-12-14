import logging
from file import File
from enum import Enum
from config import Config, get_validated_config
from typing import List, Optional
from abc import ABC, abstractmethod
from validation import validate_file, check_column_validation_rules_align_with_file_content, validate_line_values
from settings_parser import prepare_settings
from exceptions import (
    InvalidConfigException,
    InvalidLineColumnCountException,
    FoundValidationErrorException,
    FoundValidationErrorsException,
    InvalidSettingsException,
    InvalidFileLocationException,
)
from argument_parser import prepare_args


LOGGING_LEVEL = logging.DEBUG

logging.basicConfig(level=LOGGING_LEVEL)
logger = logging.getLogger(__name__)


class ValidationResultEnum(Enum):
    SUCCESS: int = 0
    FAILURE: int = 1
    COULD_NOT_PROCESS: int = 2


class ValidationBase(ABC):
    """
        class Abstract for Validation methods
    """
    def __init__(self, config: str, file_name: str) -> None:
        self.config: dict = get_validated_config(config)
        self.file_loc: str = File(self.config, file_name)
        self.settings: Settings = prepare_settings()
        logger.info(f'Validation {self}')
        self.result: List[str] = []
        
        
    @abstractmethod
    def execute_validation(self) -> object:
        ...
        
    def __repr__(self) -> str:
        return f'class name: {type(self).__name__} conf: {self.config} file: {self.file_loc}'
    

class ValidationGeneral(ValidationBase):
    def process_file_validations(self) -> None:
        """
            process file level validations function
        """
        failed_file_validations_counter: int = 0

        file_validations: dict = self.config.file_validation_rules
        file_validations_count: int = (len(file_validations) if file_validations else 0)

        if self.file_loc.file_with_configured_header_has_empty_header:
            raise InvalidConfigException(
                "File with header set to true in the config has no header row"
            )

        logger.info("Found %s file validations", file_validations_count)

        if file_validations_count > 0:
            try:
                failed_file_validations_counter = validate_file(file_validations, self.file_loc, self.result)
                if self.settings.raise_exception_and_halt_on_failed_validation \
                    and failed_file_validations_counter > 0:
                    raise FoundValidationErrorException(
                        "Evaluation of a file validation rule failed"
                    )

            except InvalidConfigException as conf_err:
                logger.error(
                    "File %s cannot be validated, config file has issues, %s",
                    self.file_loc.file_name,
                    conf_err,
                )
                raise conf_err

        if failed_file_validations_counter > 0:
            raise FoundValidationErrorsException(
                f"Evaluation of "
                f"{failed_file_validations_counter} "
                f"file validation rule(s) failed"
            )        

    def process_column_validations(self) -> None:
        """
        process column level validations function
        :return:
        """
        if self.file_loc.file_has_no_data_rows and self.settings.skip_column_validations_on_empty_file:
            logger.info("File has no rows to validate, skipping column level validations")
            return

        failed_column_validations_counter: int = 0

        check_column_validation_rules_align_with_file_content(self.config, self.file_loc, self.result)

        column_validations: dict = self.config.column_validation_rules
        column_validations_count: int = (
            len(column_validations) if column_validations else 0
        )

        logger.info("Found %s column validations", column_validations_count)

        if column_validations_count > 0:
            try:
                for idx, line in self.file_loc.file_read_generator():
                    validation_result: int = validate_line_values(
                        column_validations, line, idx
                    )
                    failed_column_validations_counter += validation_result
                    if self.settings.raise_exception_and_halt_on_failed_validation \
                        and validation_result > 0:
                        raise FoundValidationErrorException(
                            "Evaluation of a column validation rule failed"
                        )

            except InvalidConfigException as conf_err:
                logger.error(
                    "File %s cannot be validated, config file has issues, %s",
                    self.file_loc.file_name,
                    conf_err,
                )
                raise conf_err
            except InvalidLineColumnCountException as col_count_err:
                logger.error(
                    "File %s cannot be validated, column count is not consistent, %s",
                    self.file_loc.file_name,
                    col_count_err,
                )
                raise col_count_err

        if failed_column_validations_counter > 0:
            raise FoundValidationErrorsException(
                f"Evaluation of "
                f"{failed_column_validations_counter} "
                f"column validation rule(s) failed"
            )
                
    def execute_validation(self) -> ValidationResultEnum:
        accumulated_errors: str = str()
        try:
            self.process_file_validations()
        except (FoundValidationErrorException, InvalidConfigException) as halt_flow_exc:
            logger.info(
                "Failed to validate file %s , reason: %s",
                self.file_loc.file_name.file_name,
                halt_flow_exc.__str__(),
            )
            self.file_loc.close_file_handler()
            return ValidationResultEnum.FAILURE
        except FoundValidationErrorsException as found_validation_errors_continue_flow_exc:
            accumulated_errors += str(found_validation_errors_continue_flow_exc)

        try:
            self.process_column_validations()
        except (
            FoundValidationErrorException,
            InvalidConfigException,
            InvalidLineColumnCountException,
        ) as halt_flow_exc:
            logger.info(
                "Failed to validate file %s , reason: %s",
                self.file_loc.file_name,
                halt_flow_exc.__str__(),
            )            


class Factory:
    """
        1. Validar a entrada do validador.
        2. Fazer testes unitários.
        3. 
    """
    def __init__(self) -> None:
        prepared_args: dict = prepare_args()
        self.config: str = prepared_args['config']
        self.file_loc: str = prepared_args['file_loc']
        self.validate: str = prepared_args['validate']
        self.validation: dict = {}
    
    def execute(self) -> ValidationBase.execute_validation:
        self.validation = eval(self.validate)(self.config, self.file_loc)
        return self.validation.execute_validation()
        
def main() -> Factory:
    """
    main function
    :return:
        """                

    return Factory()
    

if __name__ == "__main__":
    validation = main()
    validation.execute()
    print(validation.validation.result)
