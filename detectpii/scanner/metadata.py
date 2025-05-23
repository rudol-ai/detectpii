from attr import define

from detectpii.detector import Detector, EnglishColumnNameRegexDetector
from detectpii.model import PiiColumn, Scanner, Column, Table


@define(kw_only=True)
class MetadataScanner(Scanner):
    """Scan the table schema for PII columns."""

    column_name_regex_detector: Detector = EnglishColumnNameRegexDetector()

    def scan(
        self,
        table: Table,
        column: Column,
        **kwargs,
    ) -> list[PiiColumn]:
        pii_columns = []

        pii_type = self.column_name_regex_detector.detect(column)

        if pii_type:
            pii_column = PiiColumn(
                table=table.name,
                column=column.name,
                pii_type=pii_type,
            )

            pii_columns.append(pii_column)

        return pii_columns
